import React from 'react';
import MonacoEditor from 'react-monaco-editor';
import { Card } from 'antd';
import '../styles/CodeEditor.css';

const CodeEditor = ({ value, onChange, language = 'python', height = '300px' }) => {
  const options = {
    selectOnLineNumbers: true,
    roundedSelection: false,
    readOnly: false,
    cursorStyle: 'line',
    automaticLayout: true,
    minimap: {
      enabled: true
    },
    scrollBeyondLastLine: false,
    fontSize: 14,
    fontFamily: 'Consolas, "Courier New", monospace'
  };

  return (
    <Card className="code-editor-card" bordered={false}>
      <MonacoEditor
        width="100%"
        height={height}
        language={language}
        theme="vs-dark"
        value={value}
        options={options}
        onChange={onChange}
      />
    </Card>
  );
};

export default CodeEditor;