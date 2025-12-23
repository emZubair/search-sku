#!/usr/bin/env python3
"""
Barcode Resolution Script
Matches barcodes to products, finds websites that sell them, and locates nearby shops.
"""

import argparse
import pandas as pd
import os
import logging
from dataclasses import dataclass, asdict
from typing import Dict, List


@dataclass
class BarcodeResult:
    """Represents the resolution result for a barcode query."""

    barcode: str
    product: str
    brand: str
    country: str
    websites: str
    nearby_stores: str
    confidence: str

    def to_dict(self) -> Dict:
        return asdict(self)


class BarcodeResolver:
    """Resolves product information from barcodes and locates retail locations."""

    def __init__(self, products_file: str, websites_file: str, stores_file: str):
        """
        Initialize the resolver with data files.

        Args:
            products_file: Path to products CSV/EXCEL
            websites_file: Path to websites CSV/EXCEL
            stores_file: Path to stores CSV/EXCEL
        """
        self.logger = logging.getLogger(__name__)

        self.logger.info(f"Loading products from {products_file}...")
        self.products_df = self._load_file(products_file)
        self.logger.info(f"  ✓ Loaded {len(self.products_df)} products")

        self.logger.info(f"Loading websites from {websites_file}...")
        self.websites_df = self._load_file(websites_file)
        self.logger.info(f"  ✓ Loaded {len(self.websites_df)} website entries")

        self.logger.info(f"Loading stores from {stores_file}...")
        self.stores_df = self._load_file(stores_file)
        self.logger.info(f"  ✓ Loaded {len(self.stores_df)} stores")

    def _load_file(self, filepath: str) -> pd.DataFrame:
        """Load CSV or Excel file."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        if filepath.endswith(".xlsx") or filepath.endswith(".xls"):
            return pd.read_excel(filepath)
        else:
            return pd.read_csv(filepath)

    def resolve(self, barcode: str, country: str, city: str = None) -> BarcodeResult:
        """
        Resolve barcode to product info, websites, and nearby stores.

        Args:
            barcode: Product barcode
            country: Country code or name
            city: Optional city name

        Returns:
            BarcodeResult with resolved information
        """
        self.logger.info(f"Resolving barcode: {barcode}")

        product_info = self._find_product(barcode)

        if not product_info:
            self.logger.warning("  ✗ Product not found in database")
            return self._create_result(barcode, None, None, country, [], [], "Low")

        self.logger.info(
            f"  ✓ Found product: {product_info.get('product_name')} by {product_info.get('brand')}"
        )

        websites = self._find_websites(barcode)
        self.logger.info(f"  ✓ Found {len(websites)} website(s) selling this product")

        city_info = f" in {city}" if city else ""
        nearby_stores = self._find_nearby_stores(
            country, city, product_info.get("category", "")
        )
        self.logger.info(
            f"  ✓ Found {len(nearby_stores)} nearby store(s) in {country}{city_info}"
        )

        confidence = self._calculate_confidence(product_info, websites, nearby_stores)
        self.logger.info(f"  ✓ Confidence level: {confidence}")

        return self._create_result(
            barcode,
            product_info.get("product_name"),
            product_info.get("brand"),
            country,
            websites,
            nearby_stores,
            confidence,
        )

    def _find_product(self, barcode: str) -> Dict:
        """Find product by barcode."""
        matches = self.products_df[
            self.products_df["barcode"].astype(str) == str(barcode)
        ]

        if matches.empty:
            return None

        row = matches.iloc[0]
        return {
            "product_name": row.get("product_name", ""),
            "brand": row.get("brand", ""),
            "category": row.get("category", ""),
        }

    def _find_websites(self, barcode: str) -> List[str]:
        """Find all websites that reference this barcode."""
        matches = self.websites_df[
            self.websites_df["barcode"].astype(str) == str(barcode)
        ]
        return matches["website"].unique().tolist() if not matches.empty else []

    def _find_nearby_stores(
        self, country: str, city: str = None, category: str = ""
    ) -> List[str]:
        """
        Find nearby cosmetic/skincare stores.

        Filters by:
        1. Country match (required)
        2. City match (if provided)
        3. Category overlap (if category provided)
        """
        # Normalize country input
        country_normalized = country.upper()
        filtered = self.stores_df[
            self.stores_df["country"].str.upper() == country_normalized
        ]
        if city:
            city_normalized = city.lower()
            filtered = filtered[filtered["city"].str.lower() == city_normalized]

        # Filter by category if provided (check if store sells cosmetics/skincare)
        if category:
            # Stores that have overlapping categories or are cosmetic/skincare focused
            cosmetic_categories = ["cosmetics", "skincare", "beauty", "makeup"]
            category_normalized = category.lower()

            filtered = filtered[
                (
                    filtered["store_category"]
                    .str.lower()
                    .str.contains(category_normalized, na=False)
                )
                | (
                    filtered["store_category"]
                    .str.lower()
                    .str.contains("|".join(cosmetic_categories), na=False)
                )
            ]
        else:  # Just filter for cosmetic/skincare shops
            cosmetic_categories = ["cosmetics", "skincare", "beauty", "makeup"]
            filtered = filtered[
                filtered["store_category"]
                .str.lower()
                .str.contains("|".join(cosmetic_categories), na=False)
            ]

        return filtered["store_name"].unique().tolist()

    def _score_list_length(self, items: List[str]) -> int:
        """
        Score a list of items.

        Returns 2 points if 3+ items, 1 point if 1+ items, 0 otherwise.
        """
        if len(items) >= 3:
            return 2
        elif len(items) >= 1:
            return 1
        return 0

    def _calculate_confidence(
        self, product_info: Dict, websites: List[str], nearby_stores: List[str]
    ) -> str:
        """
        Calculate confidence level based on available data.

        High: Product found + multiple websites + stores with same category
        Medium: Product found + some websites OR some stores
        Low: Product not found or minimal data
        """
        if not product_info:
            return "Low"

        confidence_score = 0

        confidence_score += 2  # Product found in database
        confidence_score += self._score_list_length(websites)
        confidence_score += self._score_list_length(nearby_stores)

        if confidence_score >= 5:
            return "High"
        elif confidence_score >= 2:
            return "Medium"
        else:
            return "Low"

    def _create_result(
        self,
        barcode: str,
        product: str,
        brand: str,
        country: str,
        websites: List[str],
        stores: List[str],
        confidence: str,
    ) -> BarcodeResult:
        """Create result as BarcodeResult dataclass."""
        return BarcodeResult(
            barcode=barcode,
            product=product or "Not found",
            brand=brand or "Unknown",
            country=country,
            websites="; ".join(websites) if websites else "None found",
            nearby_stores="; ".join(stores) if stores else "None found",
            confidence=confidence,
        )


def main():
    parser = argparse.ArgumentParser(
        description="Resolve product information from barcodes"
    )
    parser.add_argument("--barcode", required=True, help="Product barcode")
    parser.add_argument("--country", required=True, help="Country (e.g., UK, US, DE)")
    parser.add_argument("--city", required=False, help="City (optional)")
    parser.add_argument("--products", default="products.csv", help="Products data file")
    parser.add_argument("--websites", default="websites.csv", help="Websites data file")
    parser.add_argument("--stores", default="stores.csv", help="Stores data file")
    parser.add_argument(
        "--output", default="output.csv", help="Output file (csv or xlsx)"
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
    )

    logger = logging.getLogger(__name__)

    try:
        logger.info("=" * 60)
        logger.info("Barcode Resolution Tool")
        logger.info("=" * 60)

        resolver = BarcodeResolver(args.products, args.websites, args.stores)
        result = resolver.resolve(args.barcode, args.country, args.city)

        logger.info("\nSaving results...")
        output_df = pd.DataFrame([result.to_dict()])

        if args.output.endswith(".xlsx"):
            output_df.to_excel(args.output, index=False)
            logger.info(f"✓ Results saved to {args.output} (Excel format)")
        else:
            output_df.to_csv(args.output, index=False)
            logger.info(f"✓ Results saved to {args.output} (CSV format)")

        logger.info("\n" + "=" * 60)
        logger.info("Result Summary:")
        logger.info("=" * 60)
        for key, value in result.to_dict().items():
            logger.info(f"{key:15} : {value}")

    except FileNotFoundError as e:
        logger.error(f"Error: {e}")
        exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
