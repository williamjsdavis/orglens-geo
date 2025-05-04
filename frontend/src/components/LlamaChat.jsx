import React, { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import rehypeRaw from 'rehype-raw'; // Import rehypeRaw
// Remove unist-util-visit import if you added it previously
// import { visit } from 'unist-util-visit';
import {
  PaperAirplaneIcon,
  LightBulbIcon,
  XMarkIcon,
  UserCircleIcon,
} from '@heroicons/react/24/outline';
import { ChatBubbleLeftEllipsisIcon } from '@heroicons/react/24/solid';

// --- Remove the custom remarkCustomTags plugin function ---

const LlamaChat = () => {
  // ... existing state and hooks ...
  const [prompt, setPrompt] = useState('');
  const [isExpanded, setIsExpanded] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  // Use the test string or the actual streamingResponse state
  const [streamingResponse, setStreamingResponse] = useState("");
  const [isFocused, setIsFocused] = useState(false);
  const [error, setError] = useState(null);
  const inputRef = useRef(null);
  const responseRef = useRef(null);


  // ... existing useEffect and handlers ...
  useEffect(() => {
    if (responseRef.current) {
      responseRef.current.scrollTop = responseRef.current.scrollHeight;
    }
  }, [streamingResponse]);

  const handleInputFocus = () => {
    setIsFocused(true);
    if (!isExpanded && !isStreaming) {
      setIsExpanded(true);
    }
  };

  const handleInputBlur = () => {
    setIsFocused(false);
    if (isExpanded && !isStreaming && !streamingResponse) {
      setIsExpanded(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!prompt.trim() || isStreaming) return;

    setIsStreaming(true);
    setError(null);
    setStreamingResponse(''); // Clear previous response

    try {
      const response = await fetch('http://localhost:8000/api/llm_stream/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: prompt.trim() }),
      });
      if (!response.ok) throw new Error(`Server error: ${response.status}`);
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const text = decoder.decode(value, { stream: true });
        setStreamingResponse(prev => prev + text);
      }
    } catch (err) {
      console.error('Error streaming response:', err);
      setError(`Failed to get response: ${err.message}`);
    } finally {
      setIsStreaming(false);
    }
  };

  const resetChat = () => {
    setStreamingResponse('');
    setPrompt('');
    setIsStreaming(false);
    setError(null);
  };

  const closeExpanded = () => {
    if (!isStreaming) {
      setIsExpanded(false);
      setStreamingResponse(''); // Clear response on close if not streaming
    }
  };


  // Custom components for markdown rendering
  const markdownComponents = {
    // Handle custom contributor tags directly
    // When using rehypeRaw, the tag name should be lowercase
    contributor: ({ node, children, ...props }) => {
      // The 'id' attribute from the HTML tag is directly available in props
      const contributorId = props.id;
      if (!contributorId) {
        // Fallback or render nothing if id is missing
        return <span className="text-red-500">[Invalid Contributor Tag: Missing ID]</span>;
      }
      return (
        <Link
          to={`/contributors/${contributorId}`}
          className="inline-flex items-center px-2 py-0.5 rounded-md bg-indigo-100 text-indigo-800 hover:bg-indigo-200 transition-colors mx-0.5"
        >
          <UserCircleIcon className="h-3.5 w-3.5 mr-1" />
          <span className="font-medium">{children}</span>
        </Link>
      );
    }
    // You might want to add other component overrides here if needed
  };

  return (
    <div className="fixed bottom-6 left-[18vw] inset-x-0 px-4 z-40 pointer-events-none">
      <div className="max-w-3xl mx-auto">
        <div
          className={`rounded-xl bg-white shadow-lg border border-gray-200 overflow-hidden transition-all duration-300 ease-in-out pointer-events-auto ${
            isExpanded ? 'transform translate-y-0' : 'transform translate-y-2'
          }`}
          style={{ boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)' }}
        >
          {/* Expanded Response Area */}
          {isExpanded && (
            <div className="relative">
              {/* Close Button */}
              <button
                onClick={closeExpanded}
                className="absolute top-2 right-2 text-gray-500 hover:text-gray-700 p-1 rounded-full hover:bg-gray-100 transition-colors z-10"
                disabled={isStreaming}
              >
                <XMarkIcon className="h-5 w-5" />
              </button>

              {/* Content Area */}
              <div
                className={`px-5 pt-5 pb-4 transition-all duration-300 ease-in-out ${
                  streamingResponse || isStreaming ? 'min-h-[150px] max-h-[400px]' : 'min-h-[100px]'
                } overflow-y-auto`}
                ref={responseRef}
              >
                {/* ... Initial prompt suggestions ... */}
                 {!streamingResponse && !isStreaming && !error && (
                  <div className="flex items-start space-x-4">
                    <div className="flex-shrink-0 p-1 bg-indigo-100 rounded-full">
                      <LightBulbIcon className="h-5 w-5 text-indigo-600" />
                    </div>
                    <div>
                      <h3 className="font-medium text-gray-900">Ask me about your codebase</h3>
                      <p className="mt-1 text-sm text-gray-500">
                        I can help you understand contributors, repositories, and their relationships.
                        Try asking questions like:
                      </p>
                      <ul className="mt-2 space-y-1">
                        <li className="text-sm text-indigo-600 hover:underline cursor-pointer"
                            onClick={() => setPrompt("Who's the expert on the backend API?")}>
                          • Who's the expert on the backend API?
                        </li>
                        <li className="text-sm text-indigo-600 hover:underline cursor-pointer"
                            onClick={() => setPrompt("What's the main focus of the repository structure?")}>
                          • What's the main focus of the repository structure?
                        </li>
                        <li className="text-sm text-indigo-600 hover:underline cursor-pointer"
                            onClick={() => setPrompt("Who should I talk to about frontend components?")}>
                          • Who should I talk to about frontend components?
                        </li>
                      </ul>
                    </div>
                  </div>
                )}


                {/* Streaming Response with Typing Animation */}
                {(streamingResponse || isStreaming) && (
                  <div className="prose prose-sm max-w-none">
                    <div className="flex items-start space-x-3 mb-3">
                       {/* ... Llama Assistant header ... */}
                       <div className="flex-shrink-0 mt-0.5">
                        <div className="bg-gradient-to-r from-indigo-600 to-blue-500 rounded-full p-1">
                          <ChatBubbleLeftEllipsisIcon className="h-4 w-4 text-white" />
                        </div>
                      </div>
                      <p className="text-sm font-medium text-gray-900">Llama Assistant</p>
                    </div>

                    <div className="markdown-content pl-8 relative">
                      <ReactMarkdown
                        // Add rehypeRaw plugin
                        rehypePlugins={[rehypeRaw]}
                        // Keep remarkGfm if you need GitHub Flavored Markdown features
                        // remarkPlugins={[remarkGfm]} // Example if using GFM
                        components={markdownComponents}
                      >
                        {/* Render the state variable */}
                        {streamingResponse}
                      </ReactMarkdown>

                      {/* Animated typing cursor */}
                      {isStreaming && (
                        <span className="typing-cursor inline-block ml-0.5 w-0.5 h-4 align-middle bg-indigo-600 animate-blink">
                          <span className="sr-only">Typing...</span>
                        </span>
                      )}
                    </div>

                    {!isStreaming && streamingResponse && (
                       // ... Ask another question button ...
                       <div className="mt-4 flex justify-end">
                        <button
                          onClick={resetChat}
                          className="text-xs text-gray-500 hover:text-indigo-600 transition-colors"
                        >
                          Ask another question
                        </button>
                      </div>
                    )}
                  </div>
                )}

                {/* Error Message */}
                {error && (
                  // ... Error display ...
                   <div className="bg-red-50 p-3 rounded-md">
                    <p className="text-sm text-red-800">{error}</p>
                    <button
                      onClick={resetChat}
                      className="mt-2 text-xs font-medium text-red-700 hover:text-red-900"
                    >
                      Try again
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Input Area */}
          <form onSubmit={handleSubmit} className="p-3 bg-white relative">
             {/* ... Input field and submit button ... */}
             <div className="flex items-center">
              <div className="flex-grow">
                <input
                  ref={inputRef}
                  type="text"
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  onFocus={handleInputFocus}
                  onBlur={handleInputBlur}
                  placeholder="Ask about your codebase..."
                  className={`w-full py-2.5 pl-4 pr-12 rounded-full border ${
                    isFocused ? 'border-indigo-500 ring-2 ring-indigo-100' : 'border-gray-300'
                  } focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100`}
                  disabled={isStreaming}
                />
                <button
                  type="submit"
                  disabled={!prompt.trim() || isStreaming}
                  className={`absolute right-5 top-1/2 -translate-y-1/2 p-1.5 rounded-full ${
                    prompt.trim() && !isStreaming
                      ? 'bg-indigo-600 hover:bg-indigo-700'
                      : 'bg-gray-300 cursor-not-allowed'
                  } transition-colors duration-200`}
                >
                  <PaperAirplaneIcon className="h-4 w-4 text-white transform" />
                </button>
              </div>
            </div>

            {/* Loading indicator when streaming */}
            {isStreaming && (
              // ... Loading indicator ...
               <div className="absolute bottom-0 left-0 right-0 h-0.5">
                <div className="h-full bg-indigo-600 animate-pulse-gradient"></div>
              </div>
            )}
          </form>
        </div>
      </div>
    </div>
  );
};

export default LlamaChat;