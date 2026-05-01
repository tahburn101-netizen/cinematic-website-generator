# Project Handover: Cinematic Website Generator

**Date:** May 01, 2026
**Author:** Manus AI

## 1. Introduction

This document provides a comprehensive handover for the **Cinematic Website Generator** project. The goal of this project is to transform any existing website into a visually stunning, scroll-driven 3D experience with AI-generated images, deployed live on Vercel. It is designed to be a fully automated pipeline, from scraping the original site to deploying the cinematic version.

The generator is available as a web application, and can also be run locally or deployed to a persistent cloud service like Railway.

## 2. Current Status

### 2.1 Live Web Application

The Cinematic Website Generator is currently deployed and accessible at:

**[https://8080-imj20ik3khxe1ktr4esq7-11c74759.us1.manus.computer](https://8080-imj20ik3khxe1ktr4esq7-11c74759.us1.manus.computer)**

This instance is running the latest code with all fixes implemented. Users can paste a URL and initiate the generation process.

### 2.2 GitHub Repository

The complete source code for the project is hosted on GitHub:

**[https://github.com/tahburn101-netizen/cinematic-website-generator](https://github.com/tahburn101-netizen/cinematic-website-generator)**

All recent changes, including deployment configurations for Railway, have been pushed to the `main` branch.

### 2.3 Summary of Latest Changes

Significant improvements and bug fixes have been implemented to enhance the reliability, user experience, and deployment process:

*   **Nano Banana Image Integration**: The pipeline now correctly generates and injects AI-powered images (via Google Gemini) into the generated websites, replacing placeholders or third-party assets. The previous bug where image injection failed due to incorrect handling of HTML content has been resolved.
*   **Vercel Deployment Reliability**: The deployment process to Vercel has been made robust. It now guarantees public URLs by automatically disabling Vercel's SSO protection on newly created projects. This ensures that generated sites are immediately accessible without requiring user login.
*   **Mandatory QA Process**: The Quality Assurance (QA) step is now mandatory and will not be silently skipped. If Playwright (used for browser automation in QA) is not installed, the pipeline will halt with clear instructions for installation, preventing partial or unverified deployments.
*   **UI/UX Improvements**: The generated websites no longer suffer from hidden content due to overly aggressive scroll-triggered animations. Hero sections are immediately visible on load, and a fallback mechanism ensures content visibility even if JavaScript fails or is slow.
*   **Railway Deployment Configuration**: The repository now includes configuration files (`Procfile`, `railway.toml`, `nixpacks.toml`) to facilitate easy and persistent deployment of the web application to Railway, a cloud platform suitable for long-running Python processes.

## 3. Architecture Overview

The Cinematic Website Generator operates as a multi-stage pipeline, orchestrated by a Flask backend and a simple HTML/JavaScript frontend. The core logic resides in several Python modules.

### 3.1 High-Level Pipeline Flow

1.  **User Input**: A user provides a target website URL via the web UI.
2.  **Brand Analysis**: The pipeline scrapes the target URL to extract brand identity (colors, fonts, copy, niche).
3.  **Niche Reference**: Based on the brand analysis, the system identifies a high-quality reference website within the same industry niche to guide the design.
4.  **Image Generation (Nano Banana)**: AI-generated cinematic hero images and gallery assets are created using Google Gemini (referred to as 
Nano Banana) and uploaded to a CDN.
5.  **Website Construction**: The AI generates a cinematic version of the site using HTML, CSS (Tailwind-like), and 3D effects (Three.js + GSAP).
6.  **QA and Auto-Patching**: A Playwright-based QA agent visits the generated site, takes screenshots, scores it using AI vision, and applies automated patches for mobile responsiveness and layout issues.
7.  **Deployment**: The final, verified website is deployed to Vercel as a production project.

### 3.2 Key Components and Files

| File/Directory | Description |
| :--- | :--- |
| `app.py` | The Flask web server that handles API requests and orchestrates the pipeline execution. |
| `pipeline.py` | The main logic for the multi-stage generation process. |
| `modules/` | Contains the core modules: `brand_analyzer.py`, `website_builder.py`, `image_generator.py`, `qa_tester.py`, and `vercel_deployer.py`. |
| `ui/` | The frontend assets (HTML, CSS, JS) for the generator's web interface. |
| `output/` | Temporary directory where generated website files are stored before deployment. |
| `railway.toml`, `nixpacks.toml`, `Procfile` | Configuration files for cloud deployment on Railway. |

## 4. Setup and Installation

### 4.1 Local Development Environment

To run the Cinematic Website Generator locally, follow these steps:

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/tahburn101-netizen/cinematic-website-generator.git
    cd cinematic-website-generator
    ```

2.  **Install Dependencies**:
    It is recommended to use a virtual environment.
    ```bash
    pip install -r requirements.txt
    ```

3.  **Install Playwright Browsers**:
    This is required for the QA and scraping stages.
    ```bash
    playwright install chromium --with-deps
    ```

4.  **Configure Environment Variables**:
    Create a `.env` file or set these in your terminal:
    *   `OPENAI_API_KEY`: Required for brand analysis, website generation, and QA scoring.
    *   `VERCEL_TOKEN`: Required for deploying the generated sites to Vercel.
    *   `GOOGLE_API_KEY` (Optional): Required for on-demand Nano Banana image generation. If not provided, the system will fall back to a pre-generated image cache.

5.  **Start the Application**:
    ```bash
    python app.py
    ```
    The application will be available at `http://localhost:7860` (or the port specified).

### 4.2 Cloud Deployment (Railway)

The project is pre-configured for deployment to Railway. Simply connect your GitHub repository to a new Railway project. Railway will automatically detect the `nixpacks.toml` and `railway.toml` files, install the necessary system dependencies (including Chromium), and start the Flask server.

## 5. Known Issues and Roadmap

### 5.1 Items to be Implemented

*   **Custom Domain Support**: The `vercel_deployer.py` currently deploys to `.vercel.app` subdomains. Adding support for custom domains would be a significant enhancement.
*   **Persistent Database**: Currently, job information is stored in memory. For a production-grade application, this should be migrated to a persistent database like PostgreSQL or Redis.
*   **User Authentication**: The current application is open. Adding user accounts and authentication would be necessary for a public-facing service.
*   **Advanced Three.js Effects**: While the current Three.js integration is cinematic, adding more varied 3D scenes and interactions based on the brand niche would improve the visual appeal.

### 5.2 Items to be Tested

*   **Scaling and Concurrency**: Testing the pipeline with multiple concurrent generation requests to ensure the server and external APIs handle the load correctly.
*   **Cross-Browser Compatibility**: While the generated sites are tested with Chromium, thorough testing across Safari, Firefox, and various mobile browsers is needed.
*   **Edge Cases in Scraping**: Testing the brand analysis module with more complex or highly-protected websites to improve scraping robustness.

## 6. Maintenance and Troubleshooting

*   **Vercel Token Expiry**: Ensure the `VERCEL_TOKEN` used in the environment is valid and has sufficient permissions to create and manage projects.
*   **API Rate Limits**: Monitor usage of the OpenAI and Google Gemini APIs to avoid hitting rate limits during peak usage.
*   **Playwright Issues**: If the QA step fails consistently, ensure that Playwright is correctly installed and that the environment has the necessary system libraries for Chromium.

## 7. References

[1] [Vercel API Documentation](https://vercel.com/docs/rest-api)
[2] [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
[3] [Playwright Python Documentation](https://playwright.dev/python/docs/intro)
[4] [Railway Deployment Documentation](https://docs.railway.app/deploy/deployments)
