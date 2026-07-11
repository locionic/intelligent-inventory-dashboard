# Demo Frontend Walkthrough Client

This folder contains a single-page demo client built with HTML5, vanilla JavaScript, and Tailwind CSS. It connects to the Django REST API to query and manage inventory.

> [!NOTE]
> This is a demo client for video walkthrough purposes only. The Django backend (see root [README.md](../README.md)) represents the graded service layer for this assessment.

---

## How to Run the Frontend

1. Ensure the Django backend is running at `http://127.0.0.1:8000/`.
2. Start a local static file server inside this directory:
   ```bash
   # Using Python 3
   python3 -m http.server 3000
   ```
3. Open your browser and navigate to `http://localhost:3000/`.
