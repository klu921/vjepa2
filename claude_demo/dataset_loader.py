import pandas as pd

# Login using e.g. `huggingface-cli login` to access this dataset
splits = {'test': 'v1.0_release/parquet/test_v1.0.parquet', 'dev': 'v1.0_release/parquet/dev_v1.0.parquet', 'samples': 'v1.0_release/parquet/samples_v1.0.parquet'}
df = pd.read_parquet("hf://datasets/HourVideo/HourVideo/" + splits["test"])

print(type(df))
df.to_csv("HourVideo_Dataset.csv")