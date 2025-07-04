import streamlit as st
import pandas as pd
import io
import shutil
import os

st.set_page_config(page_title="Excel Comparator", layout="wide")
st.title("🔍 Excel Comparator — Multi-Column Match + Unique Viewer")

# Clear Streamlit Cache Button
cache_path = os.path.expanduser("~/.cache/streamlit")

def get_dir_size(path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.isfile(fp):
                total_size += os.path.getsize(fp)
    return total_size / (1024 * 1024)  # size in MB

cache_size_mb = get_dir_size(cache_path) if os.path.exists(cache_path) else 0
st.sidebar.write(f"🗂️ Cache Size: {cache_size_mb:.2f} MB")

if st.sidebar.button("🧹 Clear Streamlit Cache"):
    try:
        shutil.rmtree(cache_path)
        st.sidebar.success("✅ Cache cleared successfully.")
    except Exception as e:
        st.sidebar.error(f"⚠️ Error clearing cache: {e}")

file1 = st.file_uploader("📄 Upload First Excel File", type=["xlsx", "xls"])
file2 = st.file_uploader("📄 Upload Second Excel File", type=["xlsx", "xls"])

if file1 and file2:
    xls1 = pd.ExcelFile(file1)
    xls2 = pd.ExcelFile(file2)

    sheet1 = st.selectbox("📑 Select Sheet from File 1", xls1.sheet_names)
    sheet2 = st.selectbox("📑 Select Sheet from File 2", xls2.sheet_names)

    df1 = pd.read_excel(xls1, sheet_name=sheet1)
    df2 = pd.read_excel(xls2, sheet_name=sheet2)

    st.write("### 🔍 Preview — File 1")
    st.dataframe(df1.head())

    st.write("### 🔍 Preview — File 2")
    st.dataframe(df2.head())

    st.subheader("📌 Unique Values Finder")
    with st.expander("🔎 Find Unique Values from Any Column"):
        file_choice = st.radio("Choose file", ["File 1", "File 2"], horizontal=True)

        if file_choice == "File 1":
            uniq_col = st.selectbox("Select column from File 1", df1.columns, key="u1")
            if uniq_col:
                uniq_vals = sorted(df1[uniq_col].dropna().astype(str).unique())
                df_unique = pd.DataFrame(uniq_vals, columns=[f"Unique in {uniq_col}"])
                st.write(f"Found **{len(df_unique)}** unique values in **{uniq_col}** (File 1)")
                st.dataframe(df_unique)
                st.download_button("⬇️ Download CSV", df_unique.to_csv(index=False),
                                   file_name=f"unique_{uniq_col}_file1.csv", mime="text/csv")

        else:
            uniq_col = st.selectbox("Select column from File 2", df2.columns, key="u2")
            if uniq_col:
                uniq_vals = sorted(df2[uniq_col].dropna().astype(str).unique())
                df_unique = pd.DataFrame(uniq_vals, columns=[f"Unique in {uniq_col}"])
                st.write(f"Found **{len(df_unique)}** unique values in **{uniq_col}** (File 2)")
                st.dataframe(df_unique)
                st.download_button("⬇️ Download CSV", df_unique.to_csv(index=False),
                                   file_name=f"unique_{uniq_col}_file2.csv", mime="text/csv")

    st.subheader("🔧 Select Columns for Matching")
    cols1 = st.multiselect("Matching columns from File 1", df1.columns, key="cols1")
    cols2 = st.multiselect("Matching columns from File 2", df2.columns, key="cols2")

    show_merge = st.checkbox("🔀 Show Merged Matched Rows (Side-by-Side)", value=True)
    highlight_diffs = st.checkbox("🎨 Highlight Differences in Merged View", value=True)

    def detect_column_types(df, columns):
        return {col: str(df[col].dropna().map(type).mode()[0]).split("'")[-2] for col in columns if col in df}

    if cols1 and cols2:
        col_types1 = detect_column_types(df1, cols1)
        col_types2 = detect_column_types(df2, cols2)
        with st.expander("🧪 Detected Column Types"):
            st.write("**File 1 Column Types:**", col_types1)
            st.write("**File 2 Column Types:**", col_types2)

    def normalize_columns(df, columns):
        def clean(val):
            if pd.isna(val):
                return ""
            if isinstance(val, float) and val.is_integer():
                return str(int(val))
            return str(val).strip()
        return df[columns].applymap(clean).agg(" | ".join, axis=1)

    if len(cols1) != len(cols2):
        st.warning("⚠️ Please select the same number of columns from both files.")
    elif cols1 and cols2 and st.button("🔍 Compare Now"):
        df1["__key__"] = normalize_columns(df1, cols1)
        df2["__key__"] = normalize_columns(df2, cols2)

        keys1 = set(df1["__key__"])
        keys2 = set(df2["__key__"])

        match_keys = keys1 & keys2
        only1_keys = keys1 - keys2
        only2_keys = keys2 - keys1

        df_match1 = df1[df1["__key__"].isin(match_keys)].copy()
        df_match2 = df2[df2["__key__"].isin(match_keys)].copy()
        df_only1 = df1[df1["__key__"].isin(only1_keys)].drop(columns="__key__")
        df_only2 = df2[df2["__key__"].isin(only2_keys)].drop(columns="__key__")

        st.success(f"✅ Matches: {len(match_keys)} rows")
        st.info(f"📁 Only in File 1: {len(df_only1)} rows")
        st.info(f"📁 Only in File 2: {len(df_only2)} rows")

        merged = pd.DataFrame()

        if show_merge:
            df_match1.set_index("__key__", inplace=True)
            df_match2.set_index("__key__", inplace=True)

            merged = pd.merge(df_match1.add_prefix("F1_"), df_match2.add_prefix("F2_"),
                              left_index=True, right_index=True, how="inner").reset_index()
            merged.rename(columns={"__key__": "Match_Key"}, inplace=True)

            with st.expander("🎯 Merged Matched Rows"):
                st.dataframe(merged)

            if highlight_diffs:
                def highlight_diff(row):
                    styles = []
                    for col in row.index:
                        if col.startswith("F1_"):
                            match_col = col.replace("F1_", "F2_")
                            if match_col in row:
                                if row[col] != row[match_col]:
                                    styles.append("background-color: #ffcccc")
                                else:
                                    styles.append("background-color: #ccffcc")
                            else:
                                styles.append("")
                        else:
                            styles.append("")
                    return styles

                st.subheader("🎨 Highlighted Differences")
                st.dataframe(merged.style.apply(highlight_diff, axis=1))

        with st.expander("❌ Only in File 1"):
            st.dataframe(df_only1)

        with st.expander("❌ Only in File 2"):
            st.dataframe(df_only2)

        def create_excel():
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                if show_merge:
                    merged.to_excel(writer, sheet_name="Matched_SideBySide", index=False)
                df_only1.to_excel(writer, sheet_name="Only_in_File1", index=False)
                df_only2.to_excel(writer, sheet_name="Only_in_File2", index=False)
            buffer.seek(0)
            return buffer

        st.download_button("⬇️ Download All Results (Excel)",
                           create_excel(),
                           file_name="comparison_results.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
