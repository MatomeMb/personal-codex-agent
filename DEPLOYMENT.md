# Personal Codex Agent - Deployment Guide

## Overview
This guide covers deploying the Personal Codex Agent to various platforms, from local development to cloud production environments.

## Prerequisites

### System Requirements
- Python 3.8 or higher
- 4GB RAM minimum (8GB recommended)
- 2GB free disk space
- Internet connection for API calls

### Required Accounts
- **OpenAI API Key** (optional): [Get one here](https://platform.openai.com/api-keys)
- **Anthropic API Key** (optional): [Get one here](https://console.anthropic.com/)
- **Streamlit Cloud** (optional): [Sign up here](https://streamlit.io/cloud)

## Local Development Setup

### 1. Clone and Setup
```bash
# Clone the repository
git clone <your-repo-url>
cd personal-codex-agent

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration
```bash
# Copy environment template
cp env_example.txt .env

# Edit .env file with your API keys
# OPENAI_API_KEY=your_key_here
# ANTHROPIC_API_KEY=your_key_here
```

### 3. Test the System
```bash
# Run system tests
python test_system.py

# Start the application
streamlit run app.py
```

### 4. Access the Application
- Open your browser to: `http://localhost:8501`
- The application will be available locally

## Streamlit Cloud Deployment

### 1. Prepare Your Repository
```bash
# Ensure all files are committed
git add .
git commit -m "Ready for deployment"
git push origin main
```

### 2. Deploy to Streamlit Cloud
1. Go to [Streamlit Cloud](https://streamlit.io/cloud)
2. Sign in with your GitHub account
3. Click "New app"
4. Select your repository and main branch
5. Set the path to your app: `app.py`
6. Click "Deploy!"

### 3. Configure Environment Variables
In Streamlit Cloud:
1. Go to your app settings
2. Navigate to "Secrets"
3. Add your API keys:
```toml
OPENAI_API_KEY = "your_openai_key_here"
ANTHROPIC_API_KEY = "your_anthropic_key_here"
```

### 4. Access Your Deployed App
- Your app will be available at: `https://your-app-name.streamlit.app`
- Share this URL with others

## Alternative Deployment Options

### Heroku Deployment

#### 1. Create Heroku App
```bash
# Install Heroku CLI
# Create new app
heroku create your-app-name

# Set buildpacks
heroku buildpacks:set heroku/python
```

#### 2. Create Required Files
**Procfile:**
```
web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

**runtime.txt:**
```
python-3.9.18
```

#### 3. Deploy
```bash
# Add and commit files
git add .
git commit -m "Heroku deployment"

# Deploy to Heroku
git push heroku main

# Open the app
heroku open
```

### Docker Deployment

#### 1. Create Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

#### 2. Build and Run
```bash
# Build image
docker build -t personal-codex-agent .

# Run container
docker run -p 8501:8501 \
  -e OPENAI_API_KEY=your_key \
  -e ANTHROPIC_API_KEY=your_key \
  personal-codex-agent
```

### AWS/GCP Deployment

#### 1. Container Registry
```bash
# Tag for your registry
docker tag personal-codex-agent gcr.io/your-project/personal-codex-agent

# Push to registry
docker push gcr.io/your-project/personal-codex-agent
```

#### 2. Cloud Run (GCP)
```bash
# Deploy to Cloud Run
gcloud run deploy personal-codex-agent \
  --image gcr.io/your-project/personal-codex-agent \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## Environment-Specific Configuration

### Development Environment
```bash
# .env file
OPENAI_API_KEY=your_dev_key
ANTHROPIC_API_KEY=your_dev_key
VECTOR_DB_TYPE=faiss
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

### Production Environment
```bash
# Environment variables
OPENAI_API_KEY=your_prod_key
ANTHROPIC_API_KEY=your_prod_key
VECTOR_DB_TYPE=chroma
CHUNK_SIZE=1500
CHUNK_OVERLAP=300
LOG_LEVEL=INFO
```

### Staging Environment
```bash
# Environment variables
OPENAI_API_KEY=your_staging_key
ANTHROPIC_API_KEY=your_staging_key
VECTOR_DB_TYPE=faiss
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
LOG_LEVEL=DEBUG
```

## Performance Optimization

### 1. Vector Database Selection
- **FAISS**: Faster, better for production
- **ChromaDB**: More features, better for development

### 2. Chunk Size Optimization
- **Small chunks (500-1000)**: Better precision, more API calls
- **Large chunks (1500-2000)**: Better context, fewer API calls

### 3. Caching Strategy
- Enable Streamlit caching for expensive operations
- Cache document processing results
- Cache embedding generation

### 4. Resource Allocation
- **CPU**: 2+ cores recommended
- **Memory**: 4GB minimum, 8GB+ for large documents
- **Storage**: SSD recommended for vector database

## Security Considerations

### 1. API Key Management
- Never commit API keys to version control
- Use environment variables or secrets management
- Rotate keys regularly

### 2. Access Control
- Implement user authentication if needed
- Restrict document uploads to authorized users
- Monitor API usage and costs

### 3. Data Privacy
- Process documents locally when possible
- Use secure connections (HTTPS)
- Implement data retention policies

## Monitoring and Maintenance

### 1. Health Checks
```python
# Add to your app
import streamlit as st

@st.cache_data(ttl=300)
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }
```

### 2. Logging
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 3. Performance Monitoring
- Monitor API response times
- Track document processing speeds
- Monitor memory and CPU usage

## Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
# Solution: Install dependencies
pip install -r requirements.txt

# Check Python version
python --version  # Should be 3.8+
```

#### 2. API Key Issues
```bash
# Check environment variables
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY

# Verify in .env file
cat .env
```

#### 3. Memory Issues
```bash
# Reduce chunk size in .env
CHUNK_SIZE=500
CHUNK_OVERLAP=100
```

#### 4. Performance Issues
```bash
# Use FAISS instead of ChromaDB
VECTOR_DB_TYPE=faiss

# Reduce chunk overlap
CHUNK_OVERLAP=100
```

### Getting Help
1. Check the logs for error messages
2. Run the test script: `python test_system.py`
3. Verify all dependencies are installed
4. Check API key validity and quotas

## Cost Optimization

### 1. API Usage
- Monitor OpenAI/Anthropic API costs
- Use fallback responses when possible
- Implement rate limiting

### 2. Infrastructure
- Use appropriate instance sizes
- Enable auto-scaling
- Monitor resource usage

### 3. Caching
- Cache expensive operations
- Use CDN for static assets
- Implement session persistence

## Future Enhancements

### 1. Scalability
- Implement load balancing
- Add database clustering
- Use message queues for processing

### 2. Features
- Multi-user support
- Advanced analytics
- Integration with external services

### 3. Monitoring
- Advanced logging and tracing
- Performance dashboards
- Alert systems

## Conclusion

The Personal Codex Agent can be deployed to various platforms depending on your needs:

- **Local Development**: For testing and development
- **Streamlit Cloud**: Easiest deployment option
- **Heroku**: Good for small to medium applications
- **Docker**: Flexible deployment option
- **Cloud Platforms**: For enterprise applications

Choose the deployment option that best fits your requirements for scalability, cost, and maintenance overhead.

**Next Steps:**
1. Choose your deployment platform
2. Follow the platform-specific instructions
3. Configure environment variables
4. Test your deployment
5. Monitor performance and costs

For additional support, refer to the project documentation or create an issue in the repository.
