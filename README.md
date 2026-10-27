# live-nhl-predictor
This repo contains a live nhl probability predictor for matches, with the data pipeline integrated using different technologies. Everything is built to run locally on a Mac/Linux environment.

## Goal 

Predict, after every play, the probability that the home team wins the game. Build two models (logistic regression and a neural network), make them compete on the same data, and serve both models from two inference engines (Python and Rust) and compare them, and run everything on a local data pipeline (Minikube + Airflow).
