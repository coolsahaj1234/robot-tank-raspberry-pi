import React, { Component } from 'react';
import { LogViewer, StreamSettingsPanel, VIEW_MODE, XVIZLiveLoader } from 'streetscape.gl';

// Config
const LOG_URL = 'ws://localhost:8081';

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("Uncaught error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: 20, color: 'red' }}>
          <h1>Something went wrong.</h1>
          <pre>{this.state.error && this.state.error.toString()}</pre>
        </div>
      );
    }
    return this.props.children;
  }
}

class App extends Component {
  state = {
    log: null
  };

  componentDidMount() {
    // Setup Live Loader
    const log = new XVIZLiveLoader({
      logGuid: 'mock',
      bufferLength: 10,
      serverConfig: {
        defaultLogLength: 30,
        serverUrl: LOG_URL
      },
      worker: true,
      maxConcurrency: 4
    });

    log.on('error', console.error).connect();

    this.setState({ log });
  }

  render() {
    const { log } = this.state;

    if (!log) {
      return <div>Connecting to Robot...</div>;
    }

    const mapboxToken = process.env.REACT_APP_MAPBOX_TOKEN;
    // Use empty string to disable mapbox style loading if no token
    const mapStyle = mapboxToken ? "mapbox://styles/mapbox/dark-v9" : "";

    return (
      <div id="container">
        <div id="control-panel">
          <StreamSettingsPanel log={log} />
        </div>

        <div id="log-panel" style={{ width: '100%', height: '100%' }}>
          <ErrorBoundary>
            <LogViewer
              log={log}
              mapboxApiAccessToken={mapboxToken}
              mapStyle={mapStyle}
              viewMode={VIEW_MODE.TOP_DOWN} // Use TOP_DOWN for debugging
            />
          </ErrorBoundary>
        </div>
      </div>
    );
  }
}

export default App;
