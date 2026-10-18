# multi-agent-research-system
multi agent research system using agent
Research app

<<<<<<< HEAD This folder is the project root. The runnable frontend is the React app in frontend/src; the empty frontend/style.css and frontend/script.js files are not used by it.

Requires Python 3, Node.js/npm, and a .env file in this folder containing MISTRAL_API_KEY and TAVILY_API_KEY. Start both the API and frontend from this project folder:

Requires Python 3, Node.js/npm, and a .env file containing MISTRAL_API_KEY and TAVILY_API_KEY. Start the app from the project folder:

origin/main
./start.sh
On first launch, start.sh creates the Python virtual environment if needed and installs missing Python and frontend dependencies. It then starts both servers. Open http://127.0.0.1:5173, create an account, and ask a research question. Each completed report is saved under its own ID in research.sqlite3 and is available again after you log in. Mistral and Tavily keys stay in the root .env.

<<<<<<< HEAD To run only the frontend while developing, use npm run dev from frontend/. The full app needs ./start.sh so the API is running as well.

=======

origin/main To run the Tavily search tool directly in a terminal from the project folder:
./.venv/bin/python tools.py
Pass a different search query as an argument:

./.venv/bin/python tools.py "latest developments in AI"
<<<<<<< HEAD

Publish to GitHub

Create an empty repository on GitHub (do not add a README, license, or .gitignore), then run these commands from this project folder. Replace the URL with the repository URL GitHub gives you:

git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
git branch -M main
git push -u origin main
The project .gitignore keeps .env, the virtual environment, dependencies, build output, and the local research database out of GitHub. Add your API keys to .env on the computer where you run the app; do not commit that file.

=======

origin/main The SQLite database is local to this machine. To make accounts available from other devices, deploy the app and its database on a server.
