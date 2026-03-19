export {};

declare global {
  interface Window {
    // Chart.js UMD global loaded from CDN in `index.html`.
    Chart?: any;
  }
}

