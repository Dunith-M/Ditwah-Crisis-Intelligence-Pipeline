from crisis_pipeline.application.use_cases.classify_messages import run_classification
from crisis_pipeline.infrastructure.io.excel_writer import save_excel

def main():
    input_path = "data/raw/sample_messages.txt"
    output_path = "data/processed/classified_messages.xlsx"

    df = run_classification(input_path)

    save_excel(df, output_path)

    print("✅ Classification completed.")

if __name__ == "__main__":
    main()