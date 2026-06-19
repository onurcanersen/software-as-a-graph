"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import Image from "next/image"
import {
  LayoutDashboard,
  FileText,
  Settings,
  Database,
  Network,
  Zap,
  BarChart3,
  ShieldCheck,
  Brain,
  Cpu,
  Activity,
  BookMarked,
} from "lucide-react"

const navigation = [
  {
    name: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    name: "Explorer",
    href: "/explorer",
    icon: Network,
  },
  {
    name: "Statistics",
    href: "/statistics",
    icon: BarChart3,
  },
  {
    name: "Simulator",
    href: "/simulator",
    icon: Activity,
  },
  {
    name: "Analysis",
    href: "/analysis",
    icon: FileText,
  },
  {
    name: "Validation",
    href: "/validation",
    icon: ShieldCheck,
  },
  {
    name: "Train",
    href: "/train",
    icon: Brain,
  },
  {
    name: "Predict",
    href: "/predict",
    icon: Cpu,
  },
  {
    name: "Data",
    href: "/data",
    icon: Database,
  },
  {
    name: "Glossary",
    href: "/glossary",
    icon: BookMarked,
  },
  {
    name: "Settings",
    href: "/settings",
    icon: Settings,
  },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <div
      className="relative flex h-full w-64 flex-col border-r bg-gradient-to-b from-slate-50 via-white to-slate-50 dark:from-slate-950 dark:via-background dark:to-slate-950"
    >
      <div className="flex h-16 items-center border-b bg-gradient-to-r from-cyan-50 to-blue-50 dark:from-cyan-950/30 dark:to-blue-950/30 px-6">
        <Image
          src="/smart.png"
          alt="SMART Logo"
          width={32}
          height={32}
          className="rounded-lg shrink-0"
        />
        <span className="ml-3 text-lg font-bold bg-gradient-to-r from-cyan-500 to-blue-700 dark:from-cyan-400 dark:to-blue-500 bg-clip-text text-transparent whitespace-nowrap overflow-hidden">SMART</span>
      </div>

      <nav className="flex-1 space-y-1 p-4">
        {navigation.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(item.href + "/")
          const Icon = item.icon

          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                isActive
                  ? "bg-accent text-accent-foreground"
                  : "text-muted-foreground hover:bg-accent/50 hover:text-foreground"
              )}
            >
              <Icon className="h-5 w-5 shrink-0" />
              {item.name}
            </Link>
          )
        })}
      </nav>
    </div>
  )
}
