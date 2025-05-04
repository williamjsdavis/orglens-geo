'use client'

import React, { useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import logo from '../../public/logo.png';
import llama from '../../public/llama.png'; // Your user avatar
import {
    Dialog,
    DialogBackdrop,
    DialogPanel,
    TransitionChild,
} from '@headlessui/react';
import {
    Bars3Icon,
    Cog6ToothIcon, // Still needed for Mobile settings link
    FolderIcon,
    HomeIcon,
    UsersIcon,
    XMarkIcon,
} from '@heroicons/react/24/outline';
import LlamaChat from './LlamaChat';
// Unused imports removed

// --- Define App Navigation ---
const appNavigation = [
    { name: 'Dashboard', to: '/', icon: HomeIcon },
    { name: 'Repositories', to: '/repositories', icon: FolderIcon },
    { name: 'Contributors', to: '/contributors', icon: UsersIcon },
];

// Placeholder teams data
const teams = [
    { id: 1, name: 'Meta Llama', href: '#', initial: 'M', current: false },
];

// Mock user data (from old layout)
const user = {
    name: 'Zuck',
    imageUrl: llama
};

function classNames(...classes) {
    return classes.filter(Boolean).join(' ');
}

export default function Layout() {
    const [sidebarOpen, setSidebarOpen] = useState(false);

    return (
        <>
            <div className="h-full">
                {/* Mobile Sidebar Dialog (using new style structure/classes) */}
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
                            {/* Mobile Sidebar component (new style: dark bg) */}
                            <div className="flex grow flex-col gap-y-5 overflow-y-auto bg-gray-900 px-6 pb-4 ring-1 ring-white/10">
                                <div className="flex h-16 shrink-0 items-center">
                                    <img
                                        alt="App Logo"
                                        src={logo}
                                        className="h-8 w-auto"
                                    />
                                     {/* Optionally add title here if needed */}
                                </div>
                                <nav className="flex flex-1 flex-col">
                                    <ul role="list" className="flex flex-1 flex-col gap-y-7">
                                        <li>
                                            <ul role="list" className="-mx-2 space-y-1">
                                                {appNavigation.map((item) => (
                                                    <li key={item.name}>
                                                        <NavLink
                                                            to={item.to}
                                                            className={({ isActive }) =>
                                                                classNames(
                                                                    isActive
                                                                        ? 'bg-gray-800 text-white'
                                                                        : 'text-gray-400 hover:bg-gray-800 hover:text-white',
                                                                    'group flex gap-x-3 rounded-md p-2 text-sm font-semibold leading-6'
                                                                )
                                                            }
                                                            onClick={() => setSidebarOpen(false)}
                                                        >
                                                            <item.icon aria-hidden="true" className="size-6 shrink-0" />
                                                            {item.name}
                                                        </NavLink>
                                                    </li>
                                                ))}
                                            </ul>
                                        </li>
                                        <li>
                                            <div className="text-xs font-semibold leading-6 text-gray-400">Your teams</div>
                                            <ul role="list" className="-mx-2 mt-2 space-y-1">
                                                {teams.map((team) => (
                                                    <li key={team.name}>
                                                        <a
                                                            href={team.href}
                                                            className={classNames(
                                                                team.current
                                                                    ? 'bg-gray-800 text-white'
                                                                    : 'text-gray-400 hover:bg-gray-800 hover:text-white',
                                                                'group flex gap-x-3 rounded-md p-2 text-sm font-semibold leading-6'
                                                            )}
                                                        >
                                                            <span className="flex size-6 shrink-0 items-center justify-center rounded-lg border border-gray-700 bg-gray-800 text-[0.625rem] font-medium text-gray-400 group-hover:text-white">
                                                                {team.initial}
                                                            </span>
                                                            <span className="truncate">{team.name}</span>
                                                        </a>
                                                    </li>
                                                ))}
                                            </ul>
                                        </li>
                                        {/* Settings link STILL HERE ON MOBILE */}
                                        <li className="mt-auto">
                                            <a
                                                href="#"
                                                className="group -mx-2 flex gap-x-3 rounded-md p-2 text-sm font-semibold leading-6 text-gray-400 hover:bg-gray-800 hover:text-white"
                                            >
                                                <Cog6ToothIcon
                                                    aria-hidden="true"
                                                    className="size-6 shrink-0"
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

                {/* Static sidebar for desktop (using new style) */}
                <div className="hidden lg:fixed lg:inset-y-0 lg:z-50 lg:flex lg:w-72 lg:flex-col">
                    <div className="flex grow flex-col gap-y-5 overflow-y-auto bg-gray-900 px-6 pb-4">
                        <div className="flex h-16 shrink-0 items-center">
                            <img
                                alt="App Logo"
                                src={logo}
                                className="h-8 w-auto"
                            />
                            <h2 className="ml-3 text-lg font-semibold text-white">OrgLens</h2>
                        </div>
                        <nav className="flex flex-1 flex-col">
                            <ul role="list" className="flex flex-1 flex-col gap-y-7">
                                <li>
                                    <ul role="list" className="-mx-2 space-y-1">
                                        {appNavigation.map((item) => (
                                            <li key={item.name}>
                                                <NavLink
                                                    to={item.to}
                                                    className={({ isActive }) =>
                                                        classNames(
                                                            isActive
                                                                ? 'bg-gray-800 text-white'
                                                                : 'text-gray-400 hover:bg-gray-800 hover:text-white',
                                                            'group flex gap-x-3 rounded-md p-2 text-sm font-semibold leading-6'
                                                        )
                                                    }
                                                >
                                                    <item.icon aria-hidden="true" className="size-6 shrink-0" />
                                                    {item.name}
                                                </NavLink>
                                            </li>
                                        ))}
                                    </ul>
                                </li>
                                <li>
                                    <div className="text-xs font-semibold leading-6 text-gray-400">Your teams</div>
                                    <ul role="list" className="-mx-2 mt-2 space-y-1">
                                        {teams.map((team) => (
                                            <li key={team.name}>
                                                <a
                                                    href={team.href}
                                                    className={classNames(
                                                        team.current
                                                            ? 'bg-gray-800 text-white'
                                                            : 'text-gray-400 hover:bg-gray-800 hover:text-white',
                                                        'group flex gap-x-3 rounded-md p-2 text-sm font-semibold leading-6'
                                                    )}
                                                >
                                                    <span className="flex size-6 shrink-0 items-center justify-center rounded-lg border border-gray-700 bg-gray-800 text-[0.625rem] font-medium text-gray-400 group-hover:text-white">
                                                        {team.initial}
                                                    </span>
                                                    <span className="truncate">{team.name}</span>
                                                </a>
                                            </li>
                                        ))}
                                    </ul>
                                </li>
                                {/* --- Profile Link at the Bottom (Desktop) --- */}
                                {/* Replaces the Settings link specifically for desktop */}
                                <li className="-mx-6 mt-auto"> {/* Use negative margin like the new example */}
                                    <a
                                        href="#" // Placeholder link for profile page
                                        className="flex items-center gap-x-4 px-6 py-3 text-sm font-semibold leading-6 text-white hover:bg-gray-800" // Style from new example
                                    >
                                        <img
                                            alt="User Avatar"
                                            src={user.imageUrl} // Use your user image (llama)
                                            className="size-8 rounded-full bg-gray-800" // Style from new example
                                        />
                                        <span className="sr-only">Your profile</span>
                                        <span aria-hidden="true">{user.name}</span> {/* Use your user name (Zuck) */}
                                    </a>
                                </li>
                            </ul>
                        </nav>
                    </div>
                </div>

                {/* Top Bar (Mobile Only) */}
                <div className="sticky top-0 z-40 flex items-center gap-x-6 bg-gray-900 px-4 py-4 shadow-sm sm:px-6 lg:hidden">
                    <button type="button" onClick={() => setSidebarOpen(true)} className="-m-2.5 p-2.5 text-gray-400 lg:hidden">
                        <span className="sr-only">Open sidebar</span>
                        <Bars3Icon aria-hidden="true" className="size-6" />
                    </button>
                    <div className="flex-1 text-sm font-semibold leading-6 text-white">Dashboard</div>
                    <a href="#">
                        <span className="sr-only">Your profile</span>
                        <img
                            alt="User Avatar"
                            src={user.imageUrl} // Use your user image
                            className="size-8 rounded-full bg-gray-800"
                        />
                    </a>
                </div>

                {/* Main Content Area */}
                <main className="py-10 lg:pl-72 h-full">
                    <div className="px-4 sm:px-6 lg:px-8 pb-20"> {/* Added padding bottom for chat component */}
                        <Outlet />
                    </div>
                    
                    {/* Add the LlamaChat component here */}
                    <LlamaChat />
                </main>
            </div>
        </>
    );
}