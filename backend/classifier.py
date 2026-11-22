import pickle
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

DOMAINS = [
    "Machine Learning",
    "Deep Learning",
    "Healthcare AI",
    "Power Systems",
    "E-commerce AI",
]

MODEL_PATH = Path(__file__).resolve().parent / "topic_classifier.pkl"

TRAINING_DATA = [
    ("How does random forest work in tabular data?", "Machine Learning"),
    ("Explain linear regression, decision trees, and k-means clustering", "Machine Learning"),
    ("What is overfitting and how does cross validation prevent it?", "Machine Learning"),
    ("Feature scaling, PCA, and gradient boosting with scikit-learn", "Machine Learning"),
    ("Supervised vs unsupervised learning and evaluation metrics like precision recall", "Machine Learning"),
    ("Logistic regression and support vector machines for classification", "Machine Learning"),

    ("Explain backpropagation, CNNs, and transformers in neural networks", "Deep Learning"),
    ("How do LSTM and GRU networks handle sequential data?", "Deep Learning"),
    ("What is batch normalization, dropout, and Adam optimizer in PyTorch?", "Deep Learning"),
    ("Vision transformers, attention mechanism, and deep learning architectures", "Deep Learning"),
    ("Convolutional layers, pooling, and activation functions like ReLU", "Deep Learning"),
    ("Training deep neural networks with GPU and loss functions", "Deep Learning"),

    ("Using AI to predict diabetes or heart disease from patient records", "Healthcare AI"),
    ("Medical image segmentation for brain tumor or MRI scans", "Healthcare AI"),
    ("Clinical decision support, symptom triage, and healthcare diagnostics", "Healthcare AI"),
    ("Detecting disease stages from X-ray or pathology images", "Healthcare AI"),
    ("Patient health monitoring and medical risk prediction models", "Healthcare AI"),
    ("AI assisted diagnosis and biomedical data analysis", "Healthcare AI"),

    ("Smart grid load forecasting and renewable energy integration", "Power Systems"),
    ("Transformer fault detection, voltage stability, and power distribution", "Power Systems"),
    ("Electrical grid frequency control and substation monitoring", "Power Systems"),
    ("Solar and wind power generation forecasting in electrical grids", "Power Systems"),
    ("Power flow analysis, transmission lines, and electrical load balancing", "Power Systems"),
    ("Fault diagnosis in electrical power systems and smart meters", "Power Systems"),

    ("Product recommendation system for online shopping customers", "E-commerce AI"),
    ("Dynamic pricing, demand forecasting, and inventory management in retail", "E-commerce AI"),
    ("Fake review detection and customer sentiment analysis on shopping sites", "E-commerce AI"),
    ("Personalized shopping assistant and churn prediction for online stores", "E-commerce AI"),
    ("Cart abandonment prediction and recommendation engine for e-commerce", "E-commerce AI"),
    ("Automated customer support chatbot for online retail orders", "E-commerce AI"),
]


class TopicClassifier:
    def __init__(self):
        self.pipeline = self._load_or_train()

    def _load_or_train(self) -> Pipeline:
        if MODEL_PATH.exists():
            with open(MODEL_PATH, "rb") as f:
                return pickle.load(f)

        texts = [item[0] for item in TRAINING_DATA]
        labels = [item[1] for item in TRAINING_DATA]

        model = Pipeline([
            ("tfidf", TfidfVectorizer(lowercase=True, ngram_range=(1, 2))),
            ("clf", LogisticRegression(max_iter=1000)),
        ])
        model.fit(texts, labels)

        with open(MODEL_PATH, "wb") as f:
            pickle.dump(model, f)
        return model

    def predict(self, text: str) -> str:
        if not text or not text.strip():
            return "Machine Learning"
        pred = self.pipeline.predict([text])[0]
        return pred if pred in DOMAINS else "Machine Learning"


topic_classifier = TopicClassifier()
