import React, { useState } from 'react'; // Removed 'use client'
import { NavLink, Outlet } from 'react-router-dom'; // Import NavLink and Outlet
import logo from '../../public/logo.png';
import llama from '../../public/llama.png'; // Import logo from public folder
import {
  Dialog,
  DialogBackdrop,
  DialogPanel,
  Menu,
  MenuButton,
  MenuItem,
  MenuItems,
  TransitionChild,
} from '@headlessui/react';
import {
  Bars3Icon,
  BellIcon,
  // CalendarIcon, // Example - keep if needed later
  // ChartPieIcon, // Example - keep if needed later
  Cog6ToothIcon,
  // DocumentDuplicateIcon, // Example - keep if needed later
  FolderIcon, // Used for Repositories
  HomeIcon, // Used for Dashboard
  UsersIcon, // Used for Contributors
  XMarkIcon,
} from '@heroicons/react/24/outline';
import { ChevronDownIcon, MagnifyingGlassIcon } from '@heroicons/react/20/solid';

// --- Define App Navigation with React Router paths and Icons ---
const appNavigation = [
  { name: 'Dashboard', to: '/', icon: HomeIcon }, // Use 'to' for NavLink
  { name: 'Repositories', to: '/repositories', icon: FolderIcon },
  { name: 'Contributors', to: '/contributors', icon: UsersIcon },
  // Add other sections here if needed later using the example icons
  // { name: 'Team', to: '/team', icon: UsersIcon }, // Example
  // { name: 'Projects', to: '/projects', icon: FolderIcon }, // Example
];

// Placeholder data - keep as is for the layout structure
const teams = [
  { id: 1, name: 'Mock Org Team', href: '#', initial: 'M', current: false },
  // { id: 2, name: 'Tailwind Labs', href: '#', initial: 'T', current: false },
  // { id: 3, name: 'Workcation', href: '#', initial: 'W', current: false },
];
const userNavigation = [
  { name: 'Your profile', href: '#' }, // Keep as placeholder links
  { name: 'Sign out', href: '#' },
];

// Mock user data (can be replaced with real auth data later)
const user = {
    name: 'Zuck',
    imageUrl:
      llama
};

function classNames(...classes) {
  return classes.filter(Boolean).join(' ');
}

export default function Layout() { // Changed component name to Layout
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <>
      {/* Ensure html/body have h-full as suggested */}
      <div className="h-full"> {/* Added h-full based on comment */}
        {/* Mobile Sidebar Dialog */}
        <Dialog open={sidebarOpen} onClose={setSidebarOpen} className="relative z-50 lg:hidden">
          <DialogBackdrop
            transition
            className="fixed inset-0 bg-gray-900/80 transition-opacity duration-300 ease-linear data-[closed]:opacity-0"
          />

          <div className="fixed inset-0 flex">
            <DialogPanel
              transition
              className="relative mr-16 flex w-full max-w-xs flex-1 transform transition duration-300 ease-in-out data-[closed]:-translate-x-full"
            >
              <TransitionChild>
                <div className="absolute top-0 left-full flex w-16 justify-center pt-5 duration-300 ease-in-out data-[closed]:opacity-0">
                  <button type="button" onClick={() => setSidebarOpen(false)} className="-m-2.5 p-2.5">
                    <span className="sr-only">Close sidebar</span>
                    <XMarkIcon aria-hidden="true" className="size-6 text-white" />
                  </button>
                </div>
              </TransitionChild>
              {/* Mobile Sidebar component */}
              <div className="flex grow flex-col gap-y-5 overflow-y-auto bg-white px-6 pb-4">
                <div className="flex h-16 shrink-0 items-center">
                  <img
                    alt="App Logo" // Changed alt text
                    src={logo} // Use logo from public folder
                    className="h-8 w-auto"
                  />
                </div>
                <nav className="flex flex-1 flex-col">
                  <ul role="list" className="flex flex-1 flex-col gap-y-7">
                    <li>
                      <ul role="list" className="-mx-2 space-y-1">
                        {/* --- Use appNavigation with NavLink for Mobile --- */}
                        {appNavigation.map((item) => (
                          <li key={item.name}>
                            <NavLink // Use NavLink
                              to={item.to} // Use 'to' prop
                              // Use NavLink's isActive state for styling
                              className={({ isActive }) =>
                                classNames(
                                  isActive
                                    ? 'bg-gray-50 text-indigo-600'
                                    : 'text-gray-700 hover:bg-gray-50 hover:text-indigo-600',
                                  'group flex gap-x-3 rounded-md p-2 text-sm font-semibold leading-6' // Adjusted padding/text size from example
                                )
                              }
                              // Close sidebar on navigation for mobile
                              onClick={() => setSidebarOpen(false)}
                            >
                              {({ isActive }) => ( // Render prop to get isActive for icon styling
                                <>
                                  <item.icon
                                    aria-hidden="true"
                                    className={classNames(
                                      isActive ? 'text-indigo-600' : 'text-gray-400 group-hover:text-indigo-600',
                                      'size-6 shrink-0'
                                    )}
                                  />
                                  {item.name}
                                </>
                              )}
                            </NavLink>
                          </li>
                        ))}
                      </ul>
                    </li>
                    {/* Keep Teams section as placeholder */}
                    <li>
                      <div className="text-xs font-semibold leading-6 text-gray-400">Your teams</div>
                      <ul role="list" className="-mx-2 mt-2 space-y-1">
                        {teams.map((team) => (
                          <li key={team.name}>
                            <a // Keep as 'a' tag if these aren't app routes
                              href={team.href}
                              className={classNames(
                                team.current // Keep current logic for placeholders
                                  ? 'bg-gray-50 text-indigo-600'
                                  : 'text-gray-700 hover:bg-gray-50 hover:text-indigo-600',
                                'group flex gap-x-3 rounded-md p-2 text-sm font-semibold leading-6'
                              )}
                            >
                              <span
                                className={classNames(
                                  team.current
                                    ? 'border-indigo-600 text-indigo-600'
                                    : 'border-gray-200 text-gray-400 group-hover:border-indigo-600 group-hover:text-indigo-600',
                                  'flex size-6 shrink-0 items-center justify-center rounded-lg border bg-white text-[0.625rem] font-medium'
                                )}
                              >
                                {team.initial}
                              </span>
                              <span className="truncate">{team.name}</span>
                            </a>
                          </li>
                        ))}
                      </ul>
                    </li>
                    {/* Settings link */}
                    <li className="mt-auto">
                      <a // Keep as 'a' tag for placeholder
                        href="#"
                        className="group -mx-2 flex gap-x-3 rounded-md p-2 text-sm font-semibold leading-6 text-gray-700 hover:bg-gray-50 hover:text-indigo-600"
                      >
                        <Cog6ToothIcon
                          aria-hidden="true"
                          className="size-6 shrink-0 text-gray-400 group-hover:text-indigo-600"
                        />
                        Settings
                      </a>
                    </li>
                  </ul>
                </nav>
              </div>
            </DialogPanel>
          </div>
        </Dialog>

        {/* Static sidebar for desktop */}
        <div className="hidden lg:fixed lg:inset-y-0 lg:z-50 lg:flex lg:w-72 lg:flex-col">
          {/* Desktop Sidebar component */}
          <div className="flex grow flex-col gap-y-5 overflow-y-auto border-r border-gray-200 bg-white px-6 pb-4">
            <div className="flex h-16 shrink-0 items-center">
              <img
                alt="App Logo" // Changed alt text
                src={logo}
                className="h-10 w-auto"
              />
              <h2 className="ml-4 text-xl font-semibold">Llet's check</h2> {/* Added app name */}
            </div>
            <nav className="flex flex-1 flex-col">
              <ul role="list" className="flex flex-1 flex-col gap-y-7">
                <li>
                  <ul role="list" className="-mx-2 space-y-1">
                     {/* --- Use appNavigation with NavLink for Desktop --- */}
                    {appNavigation.map((item) => (
                      <li key={item.name}>
                        <NavLink // Use NavLink
                          to={item.to} // Use 'to' prop
                           // Use NavLink's isActive state for styling
                          className={({ isActive }) =>
                            classNames(
                              isActive
                                ? 'bg-gray-50 text-indigo-600'
                                : 'text-gray-700 hover:bg-gray-50 hover:text-indigo-600',
                              'group flex gap-x-3 rounded-md p-2 text-sm font-semibold leading-6'
                            )
                          }
                        >
                          {({ isActive }) => ( // Render prop for icon styling
                            <>
                              <item.icon
                                aria-hidden="true"
                                className={classNames(
                                  isActive ? 'text-indigo-600' : 'text-gray-400 group-hover:text-indigo-600',
                                  'size-6 shrink-0'
                                )}
                              />
                              {item.name}
                            </>
                          )}
                        </NavLink>
                      </li>
                    ))}
                  </ul>
                </li>
                {/* Keep Teams section as placeholder */}
                <li>
                  <div className="text-xs font-semibold leading-6 text-gray-400">Your teams</div>
                  <ul role="list" className="-mx-2 mt-2 space-y-1">
                    {teams.map((team) => (
                      <li key={team.name}>
                        <a // Keep as 'a' tag if these aren't app routes
                          href={team.href}
                          className={classNames(
                            team.current
                              ? 'bg-gray-50 text-indigo-600'
                              : 'text-gray-700 hover:bg-gray-50 hover:text-indigo-600',
                            'group flex gap-x-3 rounded-md p-2 text-sm font-semibold leading-6'
                          )}
                        >
                          <span
                            className={classNames(
                              team.current
                                ? 'border-indigo-600 text-indigo-600'
                                : 'border-gray-200 text-gray-400 group-hover:border-indigo-600 group-hover:text-indigo-600',
                              'flex size-6 shrink-0 items-center justify-center rounded-lg border bg-white text-[0.625rem] font-medium'
                            )}
                          >
                            {team.initial}
                          </span>
                          <span className="truncate">{team.name}</span>
                        </a>
                      </li>
                    ))}
                  </ul>
                </li>
                 {/* Settings link */}
                <li className="mt-auto">
                  <a // Keep as 'a' tag for placeholder
                    href="#"
                    className="group -mx-2 flex gap-x-3 rounded-md p-2 text-sm font-semibold leading-6 text-gray-700 hover:bg-gray-50 hover:text-indigo-600"
                  >
                    <Cog6ToothIcon
                      aria-hidden="true"
                      className="size-6 shrink-0 text-gray-400 group-hover:text-indigo-600"
                    />
                    Settings
                  </a>
                </li>
              </ul>
            </nav>
          </div>
        </div>

        {/* Main Content Area */}
        <div className="lg:pl-72 h-full"> {/* Added h-full */}
          {/* Sticky Top Bar */}
          <div className="sticky top-0 z-40 flex h-16 shrink-0 items-center gap-x-4 border-b border-gray-200 bg-white px-4 shadow-sm sm:gap-x-6 sm:px-6 lg:px-8">
            {/* Mobile Sidebar Toggle */}
            <button type="button" onClick={() => setSidebarOpen(true)} className="-m-2.5 p-2.5 text-gray-700 lg:hidden">
              <span className="sr-only">Open sidebar</span>
              <Bars3Icon aria-hidden="true" className="size-6" />
            </button>

            {/* Separator */}
            <div aria-hidden="true" className="h-6 w-px bg-gray-900/10 lg:hidden" /> {/* Adjusted color slightly */}

            <div className="flex flex-1 gap-x-4 self-stretch lg:gap-x-6">
              {/* Search Form (Placeholder) */}
              <form action="#" method="GET" className="relative flex flex-1"> {/* Use relative for icon positioning */}
                <label htmlFor="search-field" className="sr-only">
                  Search
                </label>
                <MagnifyingGlassIcon
                  aria-hidden="true"
                  className="pointer-events-none absolute inset-y-0 left-0 h-full w-5 text-gray-400"
                />
                <input
                  id="search-field"
                  name="search"
                  type="search"
                  placeholder="Search..."
                  className="block h-full w-full border-0 py-0 pl-8 pr-0 text-gray-900 placeholder:text-gray-400 focus:ring-0 sm:text-sm" // Simplified input style
                />
              </form>
              {/* Top Right Icons/Menu */}
              <div className="flex items-center gap-x-4 lg:gap-x-6">
                <button type="button" className="-m-2.5 p-2.5 text-gray-400 hover:text-gray-500">
                  <span className="sr-only">View notifications</span>
                  <BellIcon aria-hidden="true" className="size-6" />
                </button>

                {/* Separator */}
                <div aria-hidden="true" className="hidden lg:block lg:h-6 lg:w-px lg:bg-gray-900/10" /> {/* Adjusted color */}

                {/* Profile dropdown */}
                <Menu as="div" className="relative">
                  <MenuButton className="-m-1.5 flex items-center p-1.5">
                    <span className="sr-only">Open user menu</span>
                    <img
                      alt=""
                      src={user.imageUrl} // Use mock user data
                      className="size-8 rounded-full bg-gray-50"
                    />
                    <span className="hidden lg:flex lg:items-center">
                      <span aria-hidden="true" className="ml-4 text-sm font-semibold leading-6 text-gray-900">
                        {user.name} {/* Use mock user data */}
                      </span>
                      <ChevronDownIcon aria-hidden="true" className="ml-2 size-5 text-gray-400" />
                    </span>
                  </MenuButton>
                  <MenuItems
                    transition
                    className="absolute right-0 z-10 mt-2.5 w-32 origin-top-right rounded-md bg-white py-2 shadow-lg ring-1 ring-gray-900/5 transition focus:outline-none data-[closed]:scale-95 data-[closed]:transform data-[closed]:opacity-0 data-[enter]:duration-100 data-[enter]:ease-out data-[leave]:duration-75 data-[leave]:ease-in"
                  >
                    {userNavigation.map((item) => (
                      <MenuItem key={item.name}>
                        {({ focus }) => ( // Use focus state for styling
                          <a
                            href={item.href}
                            className={classNames(
                              focus ? 'bg-gray-50' : '',
                              'block px-3 py-1 text-sm leading-6 text-gray-900' // Adjusted padding/text size
                            )}
                          >
                            {item.name}
                          </a>
                         )}
                      </MenuItem>
                    ))}
                  </MenuItems>
                </Menu>
              </div>
            </div>
          </div>

          {/* --- Main Content Area where Pages Render --- */}
          <main className="py-10">
            <div className="px-4 sm:px-6 lg:px-8">
              {/* Outlet renders the matched child route's component */}
              <Outlet />
            </div>
          </main>
        </div>
      </div>
    </>
  );
}