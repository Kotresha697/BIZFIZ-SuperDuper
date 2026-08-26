# BizFiz Setup and Execution Guide

This document outlines the system requirements, configuration steps, and commands necessary to run the **BizFiz** project.

---

## 📋 System Requirements

Ensure the following software is installed on your system:
1. **Node.js** (v16.0.0 or later; recommended v20+)
2. **Python** (v3.8 or later, with `pip` and `venv`)
3. **MongoDB** (A local instance running on the default port `27017`)

---

## ⚙️ Project Components & Configuration

The project consists of three main components:
1. **Backend (`backend/`)**: A FastAPI server connecting to MongoDB.
2. **Lending-Application (`frontend/Lending-Application/`)**: React app for borrower profile submission.
3. **Bank-Admin (`frontend/Bank-Admin/`)**: React dashboard for bank administrators to review loan requests.

### Port Configurations
* **Backend (FastAPI)**: Runs on `http://localhost:8000`
* **Lending-Application (Borrower)**: Runs on `http://localhost:5000` (Configured in `frontend/Lending-Application/.env`)
* **Bank-Admin (Admin)**: Runs on `http://localhost:3000` (React default port)
* **MongoDB**: Runs on `mongodb://localhost:27017` (Database: `hackathon`)

---

## 🚀 Running the Project

Follow these steps to run each component of the application:

### 1. MongoDB Database
Ensure your MongoDB server is started and listening on `127.0.0.1:27017`. The backend connects to this database automatically to store and retrieve application details.

### 2. Backend Server
The backend is a Python FastAPI application. It is packaged as the `backend`
Python package, so it must be launched from the **project root** using the
package-style module path `backend.main:app` (this matches the Procfile,
`run_backend.ps1`, and the automated tests).
1. Open a new terminal at the **project root** (the folder containing `backend/`).
2. Activate the virtual environment:
   * **Windows (PowerShell)**:
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
   * **Windows (CMD)**:
     ```cmd
     .venv\Scripts\activate.bat
     ```
   * **macOS/Linux**:
     ```bash
     source .venv/bin/activate
     ```
3. Install Python dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
4. (Optional) Configure the Bank-Admin login. If these are not set, a random
   development password is generated and printed to the backend console once on
   first startup:
   ```bash
   # PowerShell example
   $env:ADMIN_USERNAME = "admin"
   $env:ADMIN_PASSWORD = "choose-a-strong-password"
   ```
5. Start the server (canonical command, run from the project root):
   ```bash
   uvicorn backend.main:app --reload --port 8000
   ```

### 3. Lending-Application (Borrower Portal)
1. Open a new terminal in `frontend/Lending-Application/`.
2. Install the frontend dependencies (handling the React 17 peer-dependency resolutions):
   ```bash
   npm install --legacy-peer-deps
   ```
3. Start the application:
   ```bash
   npm start
   ```
4. Open [http://localhost:5000](http://localhost:5000) in your browser.

### 4. Bank-Admin (Bank Dashboard)
1. Open a new terminal in `frontend/Bank-Admin/`.
2. Install the dashboard dependencies:
   ```bash
   npm install --legacy-peer-deps
   ```
3. Start the application:
   ```bash
   npm start
   ```
4. Open [http://localhost:3000](http://localhost:3000) in your browser.
