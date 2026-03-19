import React, { Component, ErrorInfo, ReactNode } from "react";

interface Props {
  children?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught error:", error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="errorBoundary glassPanel">
          <h2>Oops, something stopped working.</h2>
          <p className="muted mono">{this.state.error?.message}</p>
          <button className="btn btnPrimary" onClick={() => window.location.reload()}>Reload Dashboard</button>
        </div>
      );
    }
    return this.props.children;
  }
}
