# Barcode Resolution Script

A Python script that resolves product information from barcodes, finds websites that sell the product, and locates nearby cosmetic/skincare shops.

## Setup

### 1. Clone the repository

```bash
git clone git@github.com:emZubair/search-sku.git
cd search-sku
```

### 2. Create virtual environment

```bash
python3 -m venv venv
```

### 3. Activate virtual environment

On macOS/Linux:

```bash
source venv/bin/activate
```

On Windows:

```bash
venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

## Requirements

- Python 3.7+
- All dependencies listed in `requirements.txt`

## How to Run

### Basic Usage

```bash
python resolve_barcode.py --barcode 4005808210446 --country UK --city London
```

### Required Arguments

- `--barcode`: Product barcode (e.g., `4005808210446`)
- `--country`: Country code or name (e.g., `UK`, `US`, `DE`)

### Optional Arguments

- `--city`: City name for filtering nearby stores (e.g., `London`)
- `--products`: Path to products CSV file (default: `products.csv`)
- `--websites`: Path to websites CSV file (default: `websites.csv`)
- `--stores`: Path to stores CSV file (default: `stores.csv`)
- `--output`: Output file path (default: `output.csv`, can use `.xlsx` for Excel)

### Examples

With city specified:

```bash
python resolve_barcode.py --barcode 4005808210446 --country UK --city London
```

Output as Excel file:

```bash
python resolve_barcode.py --barcode 4005808210446 --country UK --output results.xlsx
```

## Data File Format

### products.csv

Required columns:

- `barcode`: Product barcode
- `product_name`: Name of the product
- `brand`: Brand name
- `category`: Product category (e.g., skincare, makeup, haircare)

### websites.csv

Required columns:

- `barcode`: Product barcode
- `website`: Website URL or domain

### stores.csv

Required columns:

- `store_name`: Name of the physical store
- `city`: City where the store is located
- `country`: Country (e.g., UK, US, DE)
- `store_category`: Store category (e.g., "skincare and cosmetics")

## Assumptions

1. **Barcode Matching**: The script performs exact matching on barcode values. Barcodes are normalized as strings before comparison to handle leading zeros.

2. **Country Matching**: Country names are normalized to uppercase for case-insensitive matching. The `country` parameter can be a full name (e.g., "United Kingdom") or code (e.g., "UK").

3. **City Filtering**: If a city is provided, the script filters stores that match both country AND city. City matching is case-insensitive.

4. **Category Overlap**: The script identifies cosmetic/skincare shops using category keywords:

   - `cosmetics`, `skincare`, `beauty`, `makeup`
   - If a product category is provided, stores are also filtered by category overlap

5. **Confidence Scoring**:

   - **High**: Product found + 3+ websites + 2+ stores
   - **Medium**: Product found + some websites OR some stores
   - **Low**: Product not found or minimal data

6. **Missing Data**:

   - Products not found in the database are marked as "Not found"
   - When no websites or stores are found, the result shows "None found"

7. **Data Quality**: The script assumes data files are reasonably clean. Duplicate entries in CSV files are automatically deduplicated in results.

8. **No Fuzzy Matching**: The script uses exact matches for barcodes. Fuzzy matching or partial matches are not implemented.

## Example Output

```
✓ Results saved to output.csv

Result summary:
  barcode: 4005808210446
  product: Anti-Wrinkle Eye Cream
  brand: Nivea
  country: UK
  websites: boots.com; lookfantastic.com; selfridges.com; amazon.co.uk
  nearby_stores: Boots; Superdrug; Space NK; Selfridges; Harrods; Sephora; The Body Shop
  confidence: High
```
