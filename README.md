# HumAL
HumAIne active learning platform.

## Architecture
```mermaid
  graph TD;
    Pipeline --> Data_Manager
    Pipeline --> Model_Manager
    Pipeline --> Oracle
    Pipeline --> Selection_Strategy

    Model_Manager --> Train
    Model_Manager --> Predict

    Train --> Retrain
    Train --> Incremental
    Train --> Finetuning

    Oracle --> Benchmark
    Oracle --> Human_User
```