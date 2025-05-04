// New component to hold the tooltip's inner content structure
import React from 'react';
import ReactMarkdown from 'react-markdown';

const CustomTooltipContent = ({ content }) => {
  if (!content) return null; // Should not happen if used correctly but good practice

  let truncatedSummary = content.summary;
    if (truncatedSummary && truncatedSummary.length > 500) {
        truncatedSummary = truncatedSummary.substring(0, 100) + '...';
        }

  return (
    <div className="flex items-start gap-3 z-50">
      {content.type === 'contributor' && content.avatar && (
        <img
          src={content.avatar}
          alt={content.name}
          className="w-12 h-12 rounded-full border-2 border-white shadow-sm flex-shrink-0" // Added flex-shrink-0
        />
      )}
      <div className="flex-grow"> {/* Added flex-grow */}
        <h3 className="font-bold text-lg break-words">{content.name}</h3> {/* Allow wrapping */}

        {content.type === 'repository' && (
          <>
            <p className="text-sm mt-2 break-words">{content.summary || 'No description.'}</p> {/* Allow wrapping */}
          </>
        )}

        {content.type === 'contributor' && (
          <>
            <div className="flex gap-5 mt-2">
              <div className="text-center">
                <div className="text-sm font-semibold">{content.issueCount || 0}</div>
                <div className="text-xs text-gray-500">Issues</div>
              </div>
              <div className="text-center">
                <div className="text-sm font-semibold">{content.commitCount || 0}</div>
                <div className="text-xs text-gray-500">Commits</div>
              </div>
            </div>
            {content.summary && ( // Show summary only if available
               <p className="text-sm mt-2 break-words prose"><ReactMarkdown>{truncatedSummary}</ReactMarkdown></p>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default CustomTooltipContent;
