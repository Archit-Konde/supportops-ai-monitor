FROM python:3.11-slim

# Create non-root user (HuggingFace Spaces requirement)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONPATH=/home/user/app/src

WORKDIR $HOME/app

# Install dependencies first (Docker cache optimization)
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source and config
COPY --chown=user src/ ./src/
COPY --chown=user .streamlit .streamlit

# Create runtime directories
RUN mkdir -p db data logs

EXPOSE 8501

HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1

CMD ["streamlit", "run", "src/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
