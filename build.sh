#!/bin/bash
# Download HuggingFace model during build to avoid timeout on first request

echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "🔽 Pre-downloading HuggingFace embedding model..."
python3 << EOF
from langchain_huggingface import HuggingFaceEmbeddings
print("Downloading paraphrase-albert-small-v2...")
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-albert-small-v2",
    model_kwargs={'device': 'cpu'}
)
print("✅ Model downloaded and cached!")
EOF

echo "✅ Build complete!"
