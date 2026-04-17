import { Component, type ErrorInfo, type ReactNode } from "react";

import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";
import Stack from "@mui/material/Stack";

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  public state: ErrorBoundaryState = { hasError: false };

  public static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  public componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error("ErrorBoundary caught an error", error, info);
  }

  private reset = (): void => {
    this.setState({ hasError: false });
  };

  public render(): ReactNode {
    if (!this.state.hasError) {
      return this.props.children;
    }

    return (
      <Stack p={3} spacing={2} role="alert">
        <Alert severity="error">Something broke in this section.</Alert>
        <Button variant="contained" onClick={this.reset}>
          Try again
        </Button>
      </Stack>
    );
  }
}
