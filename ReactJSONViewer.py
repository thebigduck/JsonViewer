import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { FileText, UploadCloud, Link2, LogIn, LogOut, Settings, HelpCircle, ChevronDown, ChevronRight, Search, Copy, Trash2, AlignLeft, AlignCenter, AlertTriangle, CheckCircle, XCircle, Maximize, Minimize } from 'lucide-react';

// Color Palette Constants
const PALETTE = {
  midnightGreen: '#114B5F', // Darkest
  seaGreen: '#1A936F',       // Primary action green
  celadon: '#88D498',         // Lighter green / Secondary action
  teaGreen: '#C6DABF',         // Very light green / Subtle backgrounds / Disabled
  parchment: '#F3E9D2',       // Neutral / Text on dark / Light backgrounds
};

// Mock configuration (replace with actual Okta config in a real scenario)
const MOCK_OKTA_CONFIG = {
  clientId: 'mock-client-id',
  issuer: 'https://mock.okta.com/oauth2/default',
  redirectUri: window.location.origin + '/login/callback',
  scopes: ['openid', 'profile', 'email'],
};

const WHITELISTED_URLS = [
  'https://api.example.com/data/products',
  'https://api.internal/user-settings',
  'http://localhost:3000/mock-data.json' // For local testing
];

// Sample JSON for URL fetch simulation
const MOCK_FETCHED_JSON = {
  "id": "mock-data-123",
  "name": "Fetched Product",
  "version": "1.0",
  "features": ["fast", "reliable", "secure"],
  "dimensions": {
    "width": 100,
    "height": 200,
    "unit": "cm"
  },
  "isActive": true,
  "metadata": null
};

// Default Placeholder JSON for the input field
const DEFAULT_JSON_PLACEHOLDER = JSON.stringify({
  "greeting": "Hello!",
  "instructions": "You can paste your JSON here, upload a file, or fetch from a URL.",
  "example": {
    "key1": "value1",
    "key2": true,
    "key3": [1, 2, 3],
    "key4": null
  },
  "tip": "Use the controls on the left to manage your JSON."
}, null, 2);


// Audit Logger (simulated)
const auditLog = (event, details) => {
  console.log(`[AUDIT] ${new Date().toISOString()} - ${event}:`, details);
};

// Helper to determine value type for TreeView
const getValueType = (value) => {
  if (value === null) return 'null';
  if (Array.isArray(value)) return 'array';
  return typeof value;
};

// TreeNode Component for Tree View
const TreeNode = ({ nodeKey, value, level = 0, initiallyCollapsed = false, globalCollapseAll, globalExpandAll, searchTerm, darkMode }) => {
  const [isCollapsed, setIsCollapsed] = useState(initiallyCollapsed);
  const type = getValueType(value);

  useEffect(() => {
    if (globalCollapseAll) setIsCollapsed(true);
  }, [globalCollapseAll]);

  useEffect(() => {
    if (globalExpandAll) setIsCollapsed(false);
  }, [globalExpandAll]);
  
  const toggleCollapse = () => setIsCollapsed(!isCollapsed);

  const renderValue = () => {
    if (type === 'object' || type === 'array') {
      const entries = Object.entries(value);
      const itemCount = entries.length;
      return (
        <>
          <span onClick={toggleCollapse} className="cursor-pointer hover:underline">
            {isCollapsed ? <ChevronRight size={16} className="inline mr-1" /> : <ChevronDown size={16} className="inline mr-1" />}
            {type === 'array' ? '[' : '{'}
            {isCollapsed && (
              <>
                <span className="text-gray-500 italic">... {itemCount} item{itemCount !== 1 ? 's' : ''} ...</span>
                {type === 'array' ? ']' : '}'}
              </>
            )}
          </span>
          {!isCollapsed && (
            <div style={{ marginLeft: `${(level + 1) * 1.5}rem` }} className="border-l border-gray-300 dark:border-gray-700 pl-2">
              {entries.map(([key, val]) => (
                <TreeNode 
                  key={key} 
                  nodeKey={key} 
                  value={val} 
                  level={level + 1} 
                  initiallyCollapsed={level > 1} 
                  globalCollapseAll={false} 
                  globalExpandAll={false}
                  searchTerm={searchTerm}
                  darkMode={darkMode} 
                />
              ))}
              <div style={{ marginLeft: `-${(level + 1) * 0}rem` }}>{type === 'array' ? ']' : '}'}</div>
            </div>
          )}
        </>
      );
    } else if (type === 'string') {
      return <span style={{color: darkMode ? PALETTE.celadon : PALETTE.seaGreen}}>"{value}"</span>;
    } else if (type === 'number') {
      return <span style={{color: darkMode ? PALETTE.teaGreen : PALETTE.midnightGreen}}>{value}</span>;
    } else if (type === 'boolean') {
      return <span style={{color: darkMode ? PALETTE.celadon : PALETTE.seaGreen}}>{String(value)}</span>;
    } else if (type === 'null') {
      return <span className="text-gray-500 dark:text-gray-400">null</span>;
    }
    return String(value);
  };

  const highlightSearch = (text) => {
    if (!searchTerm || !text) return text;
    const parts = String(text).split(new RegExp(`(${searchTerm})`, 'gi'));
    return parts.map((part, i) =>
      part.toLowerCase() === searchTerm.toLowerCase() ? (
        <span key={i} className="bg-yellow-300 dark:bg-yellow-500 text-black px-0.5 rounded-sm">{part}</span>
      ) : (
        part
      )
    );
  };
  
  const isMatch = searchTerm && (String(nodeKey).toLowerCase().includes(searchTerm.toLowerCase()) || String(value).toLowerCase().includes(searchTerm.toLowerCase()));

  return (
    <div className={`py-0.5 ${isMatch ? 'bg-yellow-100 dark:bg-yellow-700/50 rounded' : ''}`}>
      <strong className="mr-1" style={{color: 'var(--tree-node-key-color)'}}>{highlightSearch(nodeKey)}:</strong>
      {renderValue()}
    </div>
  );
};


// Main App Component
const App = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [jsonInput, setJsonInput] = useState(DEFAULT_JSON_PLACEHOLDER); 
  const [parsedJson, setParsedJson] = useState(null);
  const [error, setError] = useState('');
  const [viewMode, setViewMode] = useState('tree'); 
  const [urlToFetch, setUrlToFetch] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isHelpVisible, setIsHelpVisible] = useState(false);
  const [globalCollapseAll, setGlobalCollapseAll] = useState(false);
  const [globalExpandAll, setGlobalExpandAll] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [fileName, setFileName] = useState('');
  const [darkMode, setDarkMode] = useState(() => {
    const savedMode = localStorage.getItem('darkMode');
    return savedMode ? JSON.parse(savedMode) : false;
  });

  useEffect(() => {
    const root = document.documentElement;
    if (darkMode) {
      root.classList.add('dark');
      root.style.setProperty('--bg-color', PALETTE.midnightGreen);
      root.style.setProperty('--text-color', PALETTE.parchment);
      root.style.setProperty('--card-bg-color', '#2A3B47'); 
      root.style.setProperty('--input-bg-color', '#3E4C59');
      root.style.setProperty('--border-color', PALETTE.seaGreen);
      root.style.setProperty('--input-border-color', PALETTE.seaGreen);
      root.style.setProperty('--placeholder-color', PALETTE.teaGreen);
      root.style.setProperty('--icon-color', PALETTE.celadon);
      root.style.setProperty('--highlight-color', PALETTE.celadon);
      root.style.setProperty('--tree-node-key-color', PALETTE.celadon);
      root.style.setProperty('--raw-text-bg-color', '#2A3B47');
    } else { // Light Mode Refined
      root.classList.remove('dark');
      root.style.setProperty('--bg-color', PALETTE.parchment);
      root.style.setProperty('--text-color', PALETTE.midnightGreen);
      root.style.setProperty('--card-bg-color', '#FFFFFF');
      root.style.setProperty('--input-bg-color', '#FFFFFF');
      root.style.setProperty('--border-color', PALETTE.teaGreen);
      root.style.setProperty('--input-border-color', PALETTE.celadon);
      root.style.setProperty('--placeholder-color', PALETTE.celadon); 
      root.style.setProperty('--icon-color', PALETTE.seaGreen);
      root.style.setProperty('--highlight-color', PALETTE.seaGreen);
      root.style.setProperty('--tree-node-key-color', PALETTE.midnightGreen);
      root.style.setProperty('--raw-text-bg-color', PALETTE.teaGreen);
    }
    localStorage.setItem('darkMode', JSON.stringify(darkMode)); 
  }, [darkMode]);

  useEffect(() => {
    parseJson(DEFAULT_JSON_PLACEHOLDER);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleLogin = () => {
    setIsLoading(true);
    setTimeout(() => {
      const mockUser = { name: 'Demo User', email: 'demo.user@example.com', id_token: 'mock_jwt_token_string' };
      setUser(mockUser);
      setIsAuthenticated(true);
      setIsLoading(false);
      auditLog('USER_LOGIN_SUCCESS', { userId: mockUser.email });
    }, 1000);
  };

  const handleLogout = () => {
    auditLog('USER_LOGOUT', { userId: user?.email });
    setUser(null);
    setIsAuthenticated(false);
    setParsedJson(null);
    setJsonInput(DEFAULT_JSON_PLACEHOLDER); 
    setError('');
  };

  const parseJson = useCallback((input) => {
    if (!input.trim()) {
      setParsedJson(null);
      setError('');
      return;
    }
    try {
      const parsed = JSON.parse(input);
      setParsedJson(parsed);
      setError('');
      auditLog('JSON_PARSE_SUCCESS', { inputLength: input.length });
    } catch (e) {
      setParsedJson(null);
      setError(`JSON Parse Error: ${e.message}.`);
      auditLog('JSON_PARSE_ERROR', { error: e.message });
    }
  }, []);

  useEffect(() => {
    parseJson(jsonInput);
  }, [jsonInput, parseJson]);

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      setFileName(file.name);
      const reader = new FileReader();
      reader.onload = (e) => {
        setJsonInput(e.target.result);
        auditLog('FILE_UPLOADED', { fileName: file.name, type: file.type, size: file.size });
      };
      reader.onerror = () => {
        setError('Error reading file.');
        auditLog('FILE_READ_ERROR', { fileName: file.name });
      }
      if (file.type === "application/json" || file.type === "text/plain") {
        reader.readAsText(file);
      } else {
        setError("Invalid file type. Please upload a .json or .txt file.");
        auditLog('FILE_TYPE_INVALID', { fileName: file.name, type: file.type });
      }
      event.target.value = null; 
    }
  };

  const handleUrlFetch = async () => {
    if (!urlToFetch) {
      setError('Please enter a URL to fetch.');
      return;
    }
    if (!isAuthenticated) {
      setError('Please log in to fetch from URLs.');
      auditLog('URL_FETCH_ATTEMPT_UNAUTHENTICATED', { url: urlToFetch });
      return;
    }
    if (!WHITELISTED_URLS.includes(urlToFetch)) {
      setError(`URL not whitelisted: ${urlToFetch}. Only specific internal URLs are allowed.`);
      auditLog('URL_FETCH_DENIED_NOT_WHITELISTED', { url: urlToFetch, userId: user?.email });
      return;
    }

    setIsLoading(true);
    setError('');
    auditLog('URL_FETCH_STARTED', { url: urlToFetch, userId: user?.email });
    setTimeout(() => {
      console.log(`Simulating fetch from ${urlToFetch} with Authorization: Bearer ${user?.id_token}`);
      setJsonInput(JSON.stringify(MOCK_FETCHED_JSON, null, 2));
      setParsedJson(MOCK_FETCHED_JSON); 
      setIsLoading(false);
      auditLog('URL_FETCH_SUCCESS', { url: urlToFetch, userId: user?.email });
    }, 1500);
  };

  const handlePrettyPrint = () => {
    if (parsedJson) {
      try {
        const pretty = JSON.stringify(parsedJson, null, 2);
        setJsonInput(pretty);
        auditLog('JSON_FORMAT_PRETTY', { userId: user?.email });
      } catch (e) {
        setError(`Error pretty-printing: ${e.message}`);
      }
    }
  };

  const handleMinify = () => {
    if (parsedJson) {
      try {
        const minified = JSON.stringify(parsedJson);
        setJsonInput(minified);
        auditLog('JSON_FORMAT_MINIFY', { userId: user?.email });
      } catch (e) {
        setError(`Error minifying: ${e.message}`);
      }
    }
  };

  const handleCopyToClipboard = () => {
    if (jsonInput) {
      navigator.clipboard.writeText(jsonInput)
        .then(() => {
          alert('JSON copied to clipboard!'); 
          auditLog('JSON_COPIED_TO_CLIPBOARD', { userId: user?.email });
        })
        .catch(err => {
          setError(`Failed to copy: ${err}`);
          auditLog('JSON_COPY_FAILED', { error: err, userId: user?.email });
        });
    }
  };

  const handleClear = () => {
    setJsonInput(''); 
    setParsedJson(null);
    setError('');
    setUrlToFetch('');
    setFileName('');
    setSearchTerm('');
    auditLog('JSON_CLEARED', { userId: user?.email });
  };

  const triggerGlobalCollapse = () => {
    setGlobalExpandAll(false); 
    setGlobalCollapseAll(true);
    setTimeout(() => setGlobalCollapseAll(false), 0); 
  };

  const triggerGlobalExpand = () => {
    setGlobalCollapseAll(false); 
    setGlobalExpandAll(true);
    setTimeout(() => setGlobalExpandAll(false), 0); 
  };
  
  const memoizedTreeView = useMemo(() => {
    if (!parsedJson || viewMode !== 'tree') return null;
    return (
      <TreeNode 
        nodeKey="root" 
        value={parsedJson} 
        initiallyCollapsed={false} 
        globalCollapseAll={globalCollapseAll}
        globalExpandAll={globalExpandAll}
        searchTerm={searchTerm}
        darkMode={darkMode} 
      />
    );
  }, [parsedJson, viewMode, globalCollapseAll, globalExpandAll, searchTerm, darkMode]); 

  const getButtonStyle = (type = 'primary', active = false, disabled = false) => {
    let baseClasses = `p-2 rounded-md text-sm font-medium flex items-center justify-center transition-colors shadow-sm focus:outline-none focus:ring-2 focus:ring-opacity-75`;
    let styleProps = {};
    let ringColor = `var(--highlight-color)`;

    if (disabled) {
      styleProps = {
        backgroundColor: darkMode ? PALETTE.midnightGreen : PALETTE.teaGreen,
        color: darkMode ? PALETTE.seaGreen : PALETTE.celadon,
        opacity: 0.6,
        cursor: 'not-allowed',
      };
      return { className: baseClasses, style: styleProps };
    }

    if (darkMode) {
      styleProps.color = PALETTE.parchment;
      switch (type) {
        case 'primary':
          styleProps.backgroundColor = PALETTE.seaGreen;
          styleProps.color = PALETTE.midnightGreen;
          styleProps['--hover-bg-color'] = PALETTE.celadon;
          break;
        case 'secondary':
          styleProps.backgroundColor = active ? PALETTE.celadon : PALETTE.midnightGreen;
          styleProps.color = active ? PALETTE.midnightGreen : PALETTE.parchment;
          styleProps['--hover-bg-color'] = active ? PALETTE.seaGreen : PALETTE.seaGreen; // Darker hover for inactive
          break;
        case 'action':
          styleProps.backgroundColor = PALETTE.celadon;
          styleProps.color = PALETTE.midnightGreen;
          styleProps['--hover-bg-color'] = PALETTE.seaGreen;
          break;
        case 'danger':
          styleProps.backgroundColor = '#E53E3E'; 
          styleProps['--hover-bg-color'] = '#C53030'; 
          styleProps.color = PALETTE.parchment;
          break;
        default: // Default for unstyled or general buttons if any
          styleProps.backgroundColor = PALETTE.midnightGreen;
          styleProps['--hover-bg-color'] = PALETTE.seaGreen;
      }
    } else { // Light Mode Refined
      styleProps.color = PALETTE.midnightGreen; // Default text for light mode
      switch (type) {
        case 'primary':
          styleProps.backgroundColor = PALETTE.seaGreen;
          styleProps.color = PALETTE.parchment;
          styleProps['--hover-bg-color'] = PALETTE.celadon;
          break;
        case 'secondary': // For toggles like Tree/Raw view, Expand/Collapse
          styleProps.backgroundColor = active ? PALETTE.midnightGreen : PALETTE.teaGreen;
          styleProps.color = active ? PALETTE.parchment : PALETTE.midnightGreen;
          styleProps['--hover-bg-color'] = active ? PALETTE.seaGreen : PALETTE.celadon;
          break;
        case 'action': // For Format, Minify, Copy
          styleProps.backgroundColor = PALETTE.midnightGreen;
          styleProps.color = PALETTE.parchment;
          styleProps['--hover-bg-color'] = PALETTE.seaGreen;
          break;
        case 'danger':
          styleProps.backgroundColor = '#E53E3E';
          styleProps.color = PALETTE.parchment;
          styleProps['--hover-bg-color'] = '#C53030';
          break;
        default:
          styleProps.backgroundColor = PALETTE.teaGreen;
          styleProps.color = PALETTE.midnightGreen;
          styleProps['--hover-bg-color'] = PALETTE.celadon;
      }
    }
    
    baseClasses += ` focus:ring-[${ringColor}]`;

    return { 
        className: baseClasses, 
        style: styleProps,
        onMouseEnter: (e) => { if (styleProps['--hover-bg-color'] && !disabled) e.currentTarget.style.backgroundColor = styleProps['--hover-bg-color']; },
        onMouseLeave: (e) => { if (!disabled) e.currentTarget.style.backgroundColor = styleProps.backgroundColor; }
    };
  };

  if (!isAuthenticated) {
    const loginButtonProps = getButtonStyle('primary', false, isLoading);
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-4" style={{backgroundColor: 'var(--bg-color)', color: 'var(--text-color)'}}>
        <div className="p-8 rounded-xl shadow-2xl w-full max-w-md text-center" style={{backgroundColor: 'var(--card-bg-color)'}}>
          <FileText size={48} className="mx-auto mb-6" style={{color: 'var(--icon-color)'}} />
          <h1 className="text-3xl font-bold mb-2">Internal JSON Viewer</h1>
          <p className={`mb-8 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>Securely view and format JSON data.</p>
          <button
            onClick={handleLogin}
            disabled={isLoading}
            className={`${loginButtonProps.className} w-full`}
            style={loginButtonProps.style}
            onMouseEnter={loginButtonProps.onMouseEnter}
            onMouseLeave={loginButtonProps.onMouseLeave}
          >
            {isLoading ? (
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
            ) : (
              <LogIn size={20} className="mr-2" />
            )}
            {isLoading ? 'Authenticating...' : 'Login with Okta (Simulated)'}
          </button>
          <p className={`mt-4 text-xs ${darkMode ? 'text-gray-500' : 'text-gray-700'}`}>
            This is a simulated Okta login for demonstration purposes.
          </p>
        </div>
          <button 
            onClick={() => setDarkMode(!darkMode)} 
            className="fixed top-4 right-4 p-2 rounded-full transition-colors shadow-md" 
            style={{backgroundColor: darkMode ? PALETTE.celadon : PALETTE.midnightGreen, color: darkMode ? PALETTE.midnightGreen : PALETTE.parchment}}
            title={darkMode ? "Switch to Light Mode" : "Switch to Dark Mode"}
          >
            {darkMode ? '☀️' : '🌙'}
          </button>
      </div>
    );
  }
  
  const logoutButtonProps = getButtonStyle('danger');
  const loadFileButtonProps = getButtonStyle('primary');
  const fetchButtonProps = getButtonStyle('primary', false, isLoading && !!urlToFetch);
  const treeViewButtonProps = getButtonStyle('secondary', viewMode === 'tree');
  const rawTextButtonProps = getButtonStyle('secondary', viewMode === 'text');
  const prettyPrintButtonProps = getButtonStyle('action', false, !parsedJson || viewMode !== 'text');
  const minifyButtonProps = getButtonStyle('action', false, !parsedJson || viewMode !== 'text');
  const copyButtonProps = getButtonStyle('action', false, !jsonInput);
  const clearButtonProps = getButtonStyle('danger');
  const expandAllButtonProps = getButtonStyle('secondary');
  const collapseAllButtonProps = getButtonStyle('secondary');
  const helpGotItButtonProps = getButtonStyle('primary');

  return (
    <div className="min-h-screen flex flex-col" style={{backgroundColor: 'var(--bg-color)', color: 'var(--text-color)'}}>
      <header className="p-3 shadow-md" style={{backgroundColor: 'var(--card-bg-color)'}}>
        <div className="container mx-auto flex justify-between items-center">
          <div className="flex items-center">
            <FileText size={28} style={{color: 'var(--icon-color)'}} />
            <h1 className="text-xl font-semibold ml-2">Internal JSON Viewer</h1>
          </div>
          <div className="flex items-center space-x-3">
            <span className="text-sm hidden md:inline">Welcome, {user?.name || 'User'}!</span>
            <button 
                onClick={() => setDarkMode(!darkMode)} 
                className="p-2 rounded-full transition-colors shadow-md" 
                style={{backgroundColor: darkMode ? PALETTE.celadon : PALETTE.midnightGreen, color: darkMode ? PALETTE.midnightGreen : PALETTE.parchment}}
                title={darkMode ? "Switch to Light Mode" : "Switch to Dark Mode"}
            >
              {darkMode ? '☀️' : '🌙'}
            </button>
            <button onClick={() => setIsHelpVisible(true)} title="Help" className="p-2 rounded-full hover:opacity-80"><HelpCircle size={20} style={{color: 'var(--icon-color)'}} /></button>
            <button
              onClick={handleLogout}
              className={logoutButtonProps.className}
              style={logoutButtonProps.style}
              onMouseEnter={logoutButtonProps.onMouseEnter}
              onMouseLeave={logoutButtonProps.onMouseLeave}
            >
              <LogOut size={16} className="mr-1.5" /> Logout
            </button>
          </div>
        </div>
      </header>

      <main className="flex-grow container mx-auto p-3 grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="flex flex-col space-y-4">
          <div className="p-4 rounded-lg shadow" style={{backgroundColor: 'var(--card-bg-color)'}}>
            <h2 className="text-lg font-semibold mb-2">Input JSON</h2>
            <textarea
              value={jsonInput}
              onChange={(e) => setJsonInput(e.target.value)}
              placeholder="Paste your JSON here or use the placeholder..."
              className="w-full h-40 p-2 border rounded-md resize-y focus:ring-2"
              style={{
                backgroundColor: 'var(--input-bg-color)', 
                borderColor: 'var(--input-border-color)', 
                color: 'var(--text-color)',
                '--tw-ring-color': 'var(--highlight-color)',
              }}
            />
            <div className="mt-3 flex flex-col sm:flex-row sm:items-center sm:space-x-2 space-y-2 sm:space-y-0">
              <label 
                htmlFor="file-upload" 
                className={`${loadFileButtonProps.className} cursor-pointer w-full sm:w-auto`}
                style={loadFileButtonProps.style}
                onMouseEnter={loadFileButtonProps.onMouseEnter}
                onMouseLeave={loadFileButtonProps.onMouseLeave}
              >
                <UploadCloud size={18} className="mr-2" /> Load from File
              </label>
              <input id="file-upload" type="file" accept=".json,.txt" onChange={handleFileUpload} className="hidden" />
              {fileName && <span className={`text-xs truncate ${darkMode ? 'text-gray-400' : 'text-gray-600'}`} title={fileName}>{fileName}</span>}
            </div>
          </div>

          <div className="p-4 rounded-lg shadow" style={{backgroundColor: 'var(--card-bg-color)'}}>
            <h2 className="text-lg font-semibold mb-2">Fetch from URL (Whitelisted)</h2>
            <div className="flex space-x-2">
              <input
                type="url"
                value={urlToFetch}
                onChange={(e) => setUrlToFetch(e.target.value)}
                placeholder="https://api.internal/data"
                className="flex-grow p-2 border rounded-md focus:ring-2"
                style={{
                    backgroundColor: 'var(--input-bg-color)',
                    borderColor: 'var(--input-border-color)', 
                    color: 'var(--text-color)',
                    '--tw-ring-color': 'var(--highlight-color)',
                }}
              />
              <button
                onClick={handleUrlFetch}
                disabled={isLoading && !!urlToFetch}
                className={fetchButtonProps.className}
                style={fetchButtonProps.style}
                onMouseEnter={fetchButtonProps.onMouseEnter}
                onMouseLeave={fetchButtonProps.onMouseLeave}
              >
                {isLoading && urlToFetch ? <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div> : <Link2 size={18} className="mr-2" />}
                Fetch
              </button>
            </div>
          </div>
          
          <div className="p-4 rounded-lg shadow" style={{backgroundColor: 'var(--card-bg-color)'}}>
             <h2 className="text-lg font-semibold mb-3">Controls</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              <button onClick={() => setViewMode('tree')} {...treeViewButtonProps}><AlignLeft size={16} className="mr-1.5"/> Tree View</button>
              <button onClick={() => setViewMode('text')} {...rawTextButtonProps}><AlignCenter size={16} className="mr-1.5"/> Raw Text</button>
              <button onClick={handlePrettyPrint} disabled={!parsedJson || viewMode !== 'text'} {...prettyPrintButtonProps}><Settings size={16} className="mr-1.5"/> Pretty Print</button>
              <button onClick={handleMinify} disabled={!parsedJson || viewMode !== 'text'} {...minifyButtonProps}><Minimize size={16} className="mr-1.5"/> Minify</button>
              <button onClick={handleCopyToClipboard} disabled={!jsonInput} {...copyButtonProps}><Copy size={16} className="mr-1.5"/> Copy JSON</button>
              <button onClick={handleClear} {...clearButtonProps}><Trash2 size={16} className="mr-1.5"/> Clear All</button>
            </div>
            {viewMode === 'tree' && parsedJson && (
              <div className="mt-4">
                <h3 className="text-md font-semibold mb-2">Tree Controls</h3>
                <div className="flex space-x-2 mb-2">
                    <button onClick={triggerGlobalExpand} {...expandAllButtonProps}><Maximize size={16} className="mr-1.5"/> Expand All</button>
                    <button onClick={triggerGlobalCollapse} {...collapseAllButtonProps}><Minimize size={16} className="mr-1.5"/> Collapse All</button>
                </div>
                <div className="relative">
                    <input
                        type="text"
                        placeholder="Search in tree..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full p-2 pl-8 border rounded-md focus:ring-2"
                        style={{
                            backgroundColor: 'var(--input-bg-color)',
                            borderColor: 'var(--input-border-color)', 
                            color: 'var(--text-color)',
                            '--tw-ring-color': 'var(--highlight-color)',
                        }}
                    />
                    <Search size={16} className={`absolute left-2.5 top-1/2 transform -translate-y-1/2 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`} />
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="p-4 rounded-lg shadow overflow-auto" style={{backgroundColor: 'var(--card-bg-color)', maxHeight: 'calc(100vh - 120px)'}}>
          <h2 className="text-lg font-semibold mb-2 sticky top-0 z-10 p-2 -m-2" style={{backgroundColor: 'var(--card-bg-color)'}}>{viewMode === 'tree' ? 'Tree View' : 'Raw Text View'}</h2>
          {error && (
            <div className={`p-3 mb-3 rounded-md text-sm flex items-start border`} style={{backgroundColor: darkMode ? 'rgba(229, 62, 62, 0.2)' : 'rgba(254, 235, 238, 1)', color: darkMode ? '#FEB2B2' : '#E53E3E', borderColor: darkMode ? '#E53E3E' : '#FED7D7'}} role="alert">
              <AlertTriangle size={20} className="mr-2 flex-shrink-0 mt-0.5" />
              <div>
                <strong className="font-semibold">Error:</strong> {error}
              </div>
              <button onClick={() => setError('')} className="ml-auto -mr-1 -mt-1 p-1 rounded-md" style={{color: darkMode ? '#FEB2B2' : '#E53E3E'}}>
                <XCircle size={18} />
              </button>
            </div>
          )}
          {!parsedJson && !error && !jsonInput && (
            <div className={`flex flex-col items-center justify-center h-full ${darkMode ? 'text-gray-500' : 'text-gray-700'}`}>
              <FileText size={48} className="mb-4" />
              <p>No JSON data loaded.</p>
              <p className="text-sm">Paste, upload, or fetch JSON to view it here.</p>
            </div>
          )}

          {viewMode === 'tree' && parsedJson && (
            <div className="font-mono text-sm leading-relaxed">
              {memoizedTreeView}
            </div>
          )}

          {viewMode === 'text' && jsonInput && !error && (
            <pre className="p-2 rounded-md text-sm whitespace-pre-wrap break-all overflow-x-auto" style={{backgroundColor: 'var(--raw-text-bg-color)', color: 'var(--text-color)'}}>
              <code>{jsonInput}</code>
            </pre>
          )}
           {viewMode === 'text' && !jsonInput && !error && (
             <div className={`flex flex-col items-center justify-center h-full ${darkMode ? 'text-gray-500' : 'text-gray-700'}`}>
              <p>JSON will be displayed here in raw text format.</p>
            </div>
           )}
        </div>
      </main>
      
      {isHelpVisible && (
        <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center p-4 z-50 transition-opacity duration-300 ease-in-out">
          <div className="p-6 rounded-lg shadow-xl w-full max-w-lg relative" style={{backgroundColor: 'var(--card-bg-color)', color: 'var(--text-color)'}}>
            <button onClick={() => setIsHelpVisible(false)} className="absolute top-3 right-3 p-1 rounded-full hover:opacity-75">
              <XCircle size={24} style={{color: 'var(--icon-color)'}}/>
            </button>
            <h2 className="text-2xl font-semibold mb-4 flex items-center"><HelpCircle size={28} className="mr-2" style={{color: 'var(--icon-color)'}}/>JSON Viewer Help</h2>
            <div className="space-y-3 text-sm max-h-[60vh] overflow-y-auto pr-2">
              <p><strong>Input JSON:</strong> Paste directly, upload a <code>.json</code> or <code>.txt</code> file, or fetch from a whitelisted URL (requires login).</p>
              <p><strong>Views:</strong></p>
              <ul className="list-disc list-inside ml-4 space-y-1">
                <li><strong>Tree View:</strong> Displays JSON in a collapsible hierarchy. Use "Expand All" / "Collapse All" or click on individual object/array indicators ({'{...}'} or {'[...]'}). Use the search bar to highlight matching keys/values.</li>
                <li><strong>Raw Text View:</strong> Shows the JSON as plain text. Use "Pretty Print" to format with indentation or "Minify" to remove whitespace.</li>
              </ul>
              <p><strong>Controls:</strong></p>
              <ul className="list-disc list-inside ml-4 space-y-1">
                <li><strong>Format & Copy:</strong> "Pretty Print" or "Minify" (in Raw Text view), then "Copy JSON" to clipboard.</li>
                <li><strong>Clear All:</strong> Wipes the current JSON data and inputs.</li>
              </ul>
              <p><strong>Authentication:</strong> Login is simulated. In a real environment, this would use Okta for secure access.</p>
              <p><strong>URL Fetching:</strong> Only fetches from pre-approved (whitelisted) URLs. A mock access token is "sent" for demonstration.</p>
              <p><strong>Error Handling:</strong> If your JSON is invalid, an error message will appear indicating the problem.</p>
              <p><strong>Audit Logging:</strong> Key actions (login, logout, fetch, parse) are logged to the browser's developer console for auditing simulation.</p>
              <p><strong>Dark Mode:</strong> Toggle between light and dark themes using the ☀️/🌙 icon in the header. Your preference is saved locally.</p>
            </div>
             <button 
                onClick={() => setIsHelpVisible(false)} 
                className={`${helpGotItButtonProps.className} mt-6`}
                style={helpGotItButtonProps.style}
                onMouseEnter={helpGotItButtonProps.onMouseEnter}
                onMouseLeave={helpGotItButtonProps.onMouseLeave}
              >
                Got it!
              </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default App;
