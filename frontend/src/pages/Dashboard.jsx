import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useData } from '../context/DataContext';
import OrganizationGraph from '../components/OrganizationGraph';
import { 
  ChartBarIcon, 
  UserGroupIcon, 
  FolderIcon,
  CodeBracketIcon,
  CheckCircleIcon,
  ArrowPathIcon,
  CalendarIcon,
  ChartBarSquareIcon,
  ArrowTopRightOnSquareIcon,
  AdjustmentsHorizontalIcon,
} from '@heroicons/react/24/outline';
import { 
  PresentationChartBarIcon, 
  LinkIcon,
  ArrowTrendingUpIcon,
} from '@heroicons/react/20/solid';

// Format dates nicely
const formatDate = (dateString) => {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('en-US', { 
    year: 'numeric', 
    month: 'short', 
    day: 'numeric' 
  }).format(date);
};

export default function Dashboard() {
  const { isLoading, error, contributors, repositories } = useData();
  const [showSettings, setShowSettings] = useState(false);
  const [activeRepositories, setActiveRepositories] = useState([]);
  const [activeContributors, setActiveContributors] = useState([]);
  const [recentActivity, setRecentActivity] = useState([]);
  const [graphKey, setGraphKey] = useState(Date.now());
  const [graphZoomed, setGraphZoomed] = useState(false);

  // Settings for graph display
  const [settings, setSettings] = useState({
    showLabels: true,
    showAllLinks: true,
    animated: true,
  });

  // Calculate stats and prepare data once loaded
  useEffect(() => {
    if (!isLoading && contributors && repositories) {
      // Find most active repositories based on combined commits and issues
      const repoActivity = repositories.map(repo => {
        const repoIssues = contributors.flatMap(contributor =>
          contributor.works
            .filter(work => work.repository === repo.id)
            .flatMap(work => work.issues || [])
        );
        
        const repoCommits = contributors.flatMap(contributor =>
          contributor.works
            .filter(work => work.repository === repo.id)
            .flatMap(work => work.commits || [])
        );
        
        return {
          ...repo,
          activityCount: repoIssues.length + repoCommits.length,
          lastActivity: [...repoIssues, ...repoCommits]
            .map(item => new Date(item.updated_at))
            .sort((a, b) => b - a)[0] || new Date(repo.updated_at)
        };
      });
      
      // Sort by activity count, then by most recent activity
      const sortedRepos = [...repoActivity].sort((a, b) => {
        if (b.activityCount === a.activityCount) {
          return b.lastActivity - a.lastActivity;
        }
        return b.activityCount - a.activityCount;
      });
      
      setActiveRepositories(sortedRepos.slice(0, 3));
      
      // Find most active contributors based on combined commits and issues
      const contributorActivity = contributors.map(contributor => {
        const issuesCount = contributor.works.reduce(
          (acc, work) => acc + (work.issues?.length || 0), 0
        );
        
        const commitsCount = contributor.works.reduce(
          (acc, work) => acc + (work.commits?.length || 0), 0
        );
        
        return {
          ...contributor,
          activityCount: issuesCount + commitsCount
        };
      });
      
      const sortedContributors = [...contributorActivity].sort(
        (a, b) => b.activityCount - a.activityCount
      );
      
      setActiveContributors(sortedContributors.slice(0, 3));
      
      // Create recent activity timeline
      const allActivity = contributors.flatMap(contributor =>
        contributor.works.flatMap(work => {
          const repoName = repositories.find(repo => repo.id === work.repository)?.name || 'Unknown';
          
          return [
            ...(work.commits || []).map(commit => ({
              type: 'commit',
              date: new Date(commit.updated_at),
              contributor: contributor.username,
              contributorId: contributor.id,
              contributorAvatar: contributor.avatar_url,
              repository: repoName,
              repositoryId: work.repository,
              summary: commit.summary,
              url: commit.url
            })),
            ...(work.issues || []).map(issue => ({
              type: 'issue',
              date: new Date(issue.updated_at),
              contributor: contributor.username,
              contributorId: contributor.id,
              contributorAvatar: contributor.avatar_url,
              repository: repoName,
              repositoryId: work.repository,
              summary: issue.summary,
              url: issue.url
            }))
          ];
        })
      );
      
      // Sort by most recent first and limit to 5 items
      const sortedActivity = allActivity.sort((a, b) => b.date - a.date).slice(0, 5);
      setRecentActivity(sortedActivity);
    }
  }, [isLoading, contributors, repositories]);

  // Refresh the graph with new settings
  const refreshGraph = () => {
    setGraphKey(Date.now());
  };

  // Toggle graph settings menu
  const toggleSettings = () => {
    setShowSettings(prev => !prev);
  };

  // Update a specific setting
  const updateSetting = (key, value) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  // Toggle graph zoom state
  const toggleGraphZoom = () => {
    setGraphZoomed(prev => !prev);
  };

  // Calculate total stats
  const totalIssues = contributors?.reduce(
    (total, contributor) => total + contributor.works.reduce(
      (acc, work) => acc + (work.issues?.length || 0), 0
    ), 0
  ) || 0;

  const totalCommits = contributors?.reduce(
    (total, contributor) => total + contributor.works.reduce(
      (acc, work) => acc + (work.commits?.length || 0), 0
    ), 0
  ) || 0;

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col items-center justify-center min-h-[60vh]">
          <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-indigo-500 mb-4"></div>
          <h3 className="text-lg font-medium text-gray-800">Loading Organization Data</h3>
          <p className="mt-2 text-sm text-gray-500">Preparing your dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto">
        <div className="rounded-lg bg-red-50 p-8 text-center">
          <div className="h-12 w-12 text-red-500 mx-auto mb-4">⚠️</div>
          <h3 className="text-xl font-medium text-gray-800">Error loading dashboard data</h3>
          <p className="mt-2 text-gray-600">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700"
          >
            <ArrowPathIcon className="mr-2 h-4 w-4" />
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto pb-12">
      {/* Dashboard Header */}
      <div className="bg-gradient-to-r from-indigo-600 to-blue-500 rounded-lg shadow-lg mb-8 overflow-hidden">
        <div className="px-6 py-8 sm:px-10">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center">
              <PresentationChartBarIcon className="h-8 w-8 text-white mr-4" />
              <div>
                <h1 className="text-2xl font-bold text-white">Hi Zuck,</h1>
                <p className="text-indigo-100 mt-1">
                  Here's all you need to know about the Llama team.
                </p>
              </div>
            </div>
            <div className="mt-4 sm:mt-0 flex items-center space-x-4">
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-indigo-800 bg-opacity-50 text-white">
                <FolderIcon className="mr-1.5 h-4 w-4" />
                {repositories?.length || 0} Repos
              </span>
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-indigo-800 bg-opacity-50 text-white">
                <UserGroupIcon className="mr-1.5 h-4 w-4" />
                {contributors?.length || 0} Contributors
              </span>
              <span className="hidden md:inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-indigo-800 bg-opacity-50 text-white">
                <CalendarIcon className="mr-1.5 h-4 w-4" />
                {formatDate(new Date())}
              </span>
            </div>
          </div>
        </div>

        {/* Stats Cards Section */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 px-6 pb-6 sm:px-10">
          <div className="bg-white bg-opacity-90 rounded-lg p-4 shadow-sm transition-all hover:shadow-md">
            <div className="flex items-center">
              <div className="bg-indigo-100 rounded-full p-2 mr-3">
                <FolderIcon className="h-5 w-5 text-indigo-600" />
              </div>
              <div>
                <div className="font-bold text-2xl text-gray-800">{repositories?.length || 0}</div>
                <div className="text-xs text-gray-500">Repositories</div>
              </div>
            </div>
          </div>
          
          <div className="bg-white bg-opacity-90 rounded-lg p-4 shadow-sm transition-all hover:shadow-md">
            <div className="flex items-center">
              <div className="bg-blue-100 rounded-full p-2 mr-3">
                <UserGroupIcon className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <div className="font-bold text-2xl text-gray-800">{contributors?.length || 0}</div>
                <div className="text-xs text-gray-500">Contributors</div>
              </div>
            </div>
          </div>
          
          <div className="bg-white bg-opacity-90 rounded-lg p-4 shadow-sm transition-all hover:shadow-md">
            <div className="flex items-center">
              <div className="bg-green-100 rounded-full p-2 mr-3">
                <CheckCircleIcon className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <div className="font-bold text-2xl text-gray-800">{totalIssues}</div>
                <div className="text-xs text-gray-500">Resolved Issues</div>
              </div>
            </div>
          </div>
          
          <div className="bg-white bg-opacity-90 rounded-lg p-4 shadow-sm transition-all hover:shadow-md">
            <div className="flex items-center">
              <div className="bg-amber-100 rounded-full p-2 mr-3">
                <CodeBracketIcon className="h-5 w-5 text-amber-600" />
              </div>
              <div>
                <div className="font-bold text-2xl text-gray-800">{totalCommits}</div>
                <div className="text-xs text-gray-500">Total Commits</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Side Column */}
        <div className="lg:col-span-1 space-y-8 order-2 lg:order-1">
          {/* Most Active Contributors */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <div className="px-5 py-4 border-b border-gray-200 bg-gray-50 flex justify-between items-center">
              <h3 className="text-sm font-medium text-gray-900">Top Contributors</h3>
              <Link to="/contributors" className="text-xs text-indigo-600 hover:text-indigo-800 flex items-center">
                View all
                <ArrowTrendingUpIcon className="ml-1 h-3 w-3" />
              </Link>
            </div>
            <div className="divide-y divide-gray-100">
              {activeContributors.map(contributor => {
                const issuesCount = contributor.works.reduce(
                  (acc, work) => acc + (work.issues?.length || 0), 0
                );
                const commitsCount = contributor.works.reduce(
                  (acc, work) => acc + (work.commits?.length || 0), 0
                );
                
                return (
                  <Link 
                    key={contributor.id}
                    to={`/contributors/${contributor.id}`}
                    className="flex items-center px-5 py-3 hover:bg-gray-50 transition-colors group"
                  >
                    <img 
                      src={contributor.avatar_url} 
                      alt={contributor.username}
                      className="h-8 w-8 rounded-full ring-1 ring-gray-200 object-cover mr-3" 
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 group-hover:text-indigo-600 transition-colors truncate">
                        {contributor.username}
                      </p>
                      <div className="flex items-center mt-1 space-x-2">
                        <span className="text-xs text-gray-500 flex items-center">
                          <CheckCircleIcon className="h-3 w-3 mr-0.5 text-green-500" />
                          {issuesCount}
                        </span>
                        <span className="text-xs text-gray-500 flex items-center">
                          <CodeBracketIcon className="h-3 w-3 mr-0.5 text-indigo-500" />
                          {commitsCount}
                        </span>
                      </div>
                    </div>
                    <ArrowTopRightOnSquareIcon className="h-4 w-4 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                  </Link>
                );
              })}
              {activeContributors.length === 0 && (
                <div className="px-5 py-4 text-sm text-gray-500 text-center">
                  No contributors found
                </div>
              )}
            </div>
          </div>
          
          {/* Active Repositories */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <div className="px-5 py-4 border-b border-gray-200 bg-gray-50 flex justify-between items-center">
              <h3 className="text-sm font-medium text-gray-900">Active Repositories</h3>
              <Link to="/repositories" className="text-xs text-indigo-600 hover:text-indigo-800 flex items-center">
                View all
                <ArrowTrendingUpIcon className="ml-1 h-3 w-3" />
              </Link>
            </div>
            <div className="divide-y divide-gray-100">
              {activeRepositories.map(repo => (
                <Link 
                  key={repo.id}
                  to={`/repositories/${repo.id}`}
                  className="flex flex-col px-5 py-3 hover:bg-gray-50 transition-colors group"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <FolderIcon className="h-4 w-4 text-indigo-500 mr-2 flex-shrink-0" />
                      <span className="text-sm font-medium text-gray-900 group-hover:text-indigo-600 transition-colors truncate">
                        {repo.name}
                      </span>
                    </div>
                    <ArrowTopRightOnSquareIcon className="h-4 w-4 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>
                  <div className="flex items-center mt-1.5 ml-6 space-x-3">
                    <span className="text-xs text-gray-500">
                      {repo.activityCount} activities
                    </span>
                    <span className="text-xs text-gray-500">
                      Updated {formatDate(repo.lastActivity)}
                    </span>
                  </div>
                </Link>
              ))}
              {activeRepositories.length === 0 && (
                <div className="px-5 py-4 text-sm text-gray-500 text-center">
                  No repositories found
                </div>
              )}
            </div>
          </div>
          
          {/* Recent Activity Timeline */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <div className="px-5 py-4 border-b border-gray-200 bg-gray-50">
              <h3 className="text-sm font-medium text-gray-900">Recent Activity</h3>
            </div>
            <div className="px-5 py-4">
              <ol className="relative border-l border-gray-200 ml-3 space-y-6">
                {recentActivity.map((item, idx) => (
                  <li key={idx} className="ml-6">
                    <span className={`absolute flex items-center justify-center w-6 h-6 rounded-full -left-3 ring-4 ring-white ${
                      item.type === 'commit' ? 'bg-indigo-100' : 'bg-green-100'
                    }`}>
                      {item.type === 'commit' ? 
                        <CodeBracketIcon className="w-3 h-3 text-indigo-600" /> : 
                        <CheckCircleIcon className="w-3 h-3 text-green-600" />
                      }
                    </span>
                    <div className="ml-1">
                      <div className="flex items-center">
                        <Link to={`/contributors/${item.contributorId}`} className="flex items-center mr-2">
                          <img 
                            src={item.contributorAvatar} 
                            alt={item.contributor}
                            className="w-4 h-4 rounded-full mr-1"
                          />
                          <span className="text-xs text-gray-600 hover:text-indigo-600 transition-colors">
                            {item.contributor}
                          </span>
                        </Link>
                        <time className="block text-xs font-normal leading-none text-gray-500">
                          {formatDate(item.date)}
                        </time>
                      </div>
                      <a 
                        href={item.url} 
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block text-sm font-medium text-gray-900 hover:text-indigo-600 hover:underline mt-1"
                      >
                        {item.summary.length > 60 ? `${item.summary.substring(0, 60)}...` : item.summary}
                      </a>
                      <Link 
                        to={`/repositories/${item.repositoryId}`}
                        className="text-xs text-gray-500 hover:text-indigo-600 transition-colors flex items-center mt-1"
                      >
                        <FolderIcon className="w-3 h-3 mr-1" />
                        {item.repository}
                      </Link>
                    </div>
                  </li>
                ))}
                {recentActivity.length === 0 && (
                  <p className="text-sm text-gray-500">No recent activity</p>
                )}
              </ol>
            </div>
          </div>
        </div>

        {/* Main Visualization Area */}
        <div className={`lg:col-span-3 order-1 lg:order-2 ${graphZoomed ? 'lg:col-span-4' : ''}`}>
          {/* Graph Container with Controls */}
          <div className={`bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden transition-all duration-300 ${graphZoomed ? 'h-[800px]' : 'h-[600px]'}`}>
            <div className="px-5 py-4 border-b border-gray-200 flex justify-between items-center">
              <div className="flex items-center">
                <ChartBarSquareIcon className="h-5 w-5 text-indigo-500 mr-2" />
                <h2 className="text-lg font-medium text-gray-900">Organization Network</h2>
              </div>
              <div className="flex items-center space-x-3">
                <button
                  onClick={refreshGraph}
                  className="inline-flex items-center text-xs text-gray-600 hover:text-indigo-600 transition-colors"
                  title="Refresh visualization"
                >
                  <ArrowPathIcon className="h-4 w-4" />
                </button>
                <button
                  onClick={toggleSettings}
                  className={`inline-flex items-center text-xs ${showSettings ? 'text-indigo-600' : 'text-gray-600 hover:text-indigo-600'} transition-colors`}
                  title="Visualization settings"
                >
                  <AdjustmentsHorizontalIcon className="h-4 w-4" />
                </button>
                <button
                  onClick={toggleGraphZoom}
                  className="inline-flex items-center text-xs text-gray-600 hover:text-indigo-600 transition-colors"
                  title={graphZoomed ? "Reduce graph size" : "Expand graph"}
                >
                  {graphZoomed ? (
                    <svg className="h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 9V4.5M9 9H4.5M15 9H19.5M15 9V4.5M15 15H9M15 15v4.5M15 15h4.5M9 15v4.5" />
                    </svg>
                  ) : (
                    <svg className="h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3.75v4.5m0-4.5h4.5m-4.5 0L9 9M3.75 20.25v-4.5m0 4.5h4.5m-4.5 0L9 15M20.25 3.75h-4.5m4.5 0v4.5m0-4.5L15 9m5.25 11.25h-4.5m4.5 0v-4.5m0 4.5L15 15" />
                    </svg>
                  )}
                </button>
              </div>
            </div>
            
            {/* Settings Panel */}
            {showSettings && (
              <div className="bg-gray-50 px-5 py-3 border-b border-gray-200">
                <div className="flex flex-wrap gap-4">
                  <label className="inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      className="sr-only peer"
                      checked={settings.showLabels}
                      onChange={() => updateSetting('showLabels', !settings.showLabels)}
                    />
                    <div className="relative w-9 h-5 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-indigo-300 rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-indigo-600"></div>
                    <span className="ml-2 text-xs text-gray-700">Show labels</span>
                  </label>
                  <label className="inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      className="sr-only peer"
                      checked={settings.showAllLinks}
                      onChange={() => updateSetting('showAllLinks', !settings.showAllLinks)}
                    />
                    <div className="relative w-9 h-5 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-indigo-300 rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-indigo-600"></div>
                    <span className="ml-2 text-xs text-gray-700">Show all connections</span>
                  </label>
                  <label className="inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      className="sr-only peer"
                      checked={settings.animated}
                      onChange={() => updateSetting('animated', !settings.animated)}
                    />
                    <div className="relative w-9 h-5 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-indigo-300 rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-indigo-600"></div>
                    <span className="ml-2 text-xs text-gray-700">Animated</span>
                  </label>
                  <button
                    onClick={refreshGraph}
                    className="text-xs bg-indigo-50 hover:bg-indigo-100 text-indigo-600 px-2 py-1 rounded flex items-center"
                  >
                    <ArrowPathIcon className="h-3 w-3 mr-1" />
                    Apply changes
                  </button>
                </div>
              </div>
            )}
            
            {/* Graph Visualization */}
            <div className="relative h-full">
              {contributors?.length === 0 || repositories?.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center p-8 text-center">
                  <ChartBarIcon className="h-12 w-12 text-gray-300 mb-3" />
                  <h3 className="text-lg font-medium text-gray-800">No data to visualize</h3>
                  <p className="mt-1 text-gray-500 max-w-md">
                    Add repositories and contributors to see the organization network visualization.
                  </p>
                </div>
              ) : (
                <div className="h-full">
                  <OrganizationGraph 
                    key={graphKey}
                    contributors={contributors} 
                    repositories={repositories} 
                    showLabels={settings.showLabels}
                    showAllLinks={settings.showAllLinks}
                    animated={settings.animated}
                  />
                </div>
              )}

              {/* Graph Legend */}
              <div className="absolute top-4 right-4 bg-white bg-opacity-80 p-3 rounded-lg shadow-sm border border-gray-100">
                <div className="text-xs font-medium text-gray-700 mb-2">Legend</div>
                <div className="space-y-1.5">
                  <div className="flex items-center">
                    <div className="w-3 h-3 rounded-full bg-indigo-500 mr-2"></div>
                    <span className="text-xs text-gray-600">Repository</span>
                  </div>
                  <div className="flex items-center">
                    <div className="w-3 h-3 rounded-full bg-green-500 mr-2"></div>
                    <span className="text-xs text-gray-600">Contributor</span>
                  </div>
                  <div className="flex items-center">
                    <div className="w-8 h-0.5 bg-gray-300 mr-2"></div>
                    <span className="text-xs text-gray-600">Connection</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}