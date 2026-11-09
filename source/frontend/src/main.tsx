import React from "react";
import ReactDOM from "react-dom/client";
import App from "./app";
import "./index.css";
import { applyPrefs, loadPrefs } from "./utils/preferences";

applyPrefs(loadPrefs());
window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => applyPrefs(loadPrefs()));

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
