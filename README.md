# Excel File Comparator (Multi-Column Support)

A **Streamlit** app for comparing two Excel files on selected columns (with support for using multiple columns as a composite key).

## Features

- Upload two Excel files and select sheets for comparison
- Pick multiple columns from each file to define the comparison key
- Instantly see:
  - Matched rows (keys present in both)
  - Rows unique to File 1
  - Rows unique to File 2
- Download matches and differences as Excel or CSV files

## Usage

1. Install requirements:
    ```bash
    pip install -r requirements.txt
    ```

2. Launch the app:
    ```bash
    streamlit run streamlit_excel_multi_compare.py
    ```

3. Open the provided local URL in your browser

---

**Perfect for data validation, deduplication, and reconciliation tasks involving Excel!**# streamlit-excel-compare
A **Streamlit** app for comparing two Excel files on selected columns (with support for using multiple columns as a composite key).
