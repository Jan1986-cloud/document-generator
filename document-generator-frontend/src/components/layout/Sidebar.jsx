import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { 
  LayoutDashboard, 
  Users, 
  Package, 
  ShoppingCart, 
  FileText, 
  Settings,
  ChevronLeft,
  ChevronRight,
  Building2
} from 'lucide-react'
import { cn } from '@/lib/utils.js'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/contexts/AuthContext'

const navigationItems = [
  {
    name: 'Dashboard',
    href: '/dashboard',
    icon: LayoutDashboard,
    permission: 'view_dashboard'
  },
  {
    name: 'Klanten',
    href: '/customers',
    icon: Users,
    permission: 'view_customers'
  },
  {
    name: 'Producten',
    href: '/products',
    icon: Package,
    permission: 'view_products'
  },
  {
    name: 'Opdrachten',
    href: '/orders',
    icon: ShoppingCart,
    permission: 'view_orders'
  },
  {
    name: 'Documenten',
    href: '/documents',
    icon: FileText,
    permission: 'view_documents'
  },
  {
    name: 'Instellingen',
    href: '/settings',
    icon: Settings,
    permission: 'view_settings'
  }
]

export default function Sidebar({ isOpen, onToggle }) {
  const location = useLocation()
  const { user, hasPermission } = useAuth()

  // Filter navigation items based on user permissions
  const visibleItems = navigationItems.filter(item => 
    !item.permission || hasPermission(item.permission)
  )

  return (
    <div className={cn(
      'bg-sidebar border-r border-sidebar-border transition-all duration-300 ease-in-out flex flex-col',
      isOpen ? 'w-64' : 'w-16'
    )}>
      {/* Header */}
      <div className="p-4 border-b border-sidebar-border">
        <div className="flex items-center justify-between">
          {isOpen && (
            <div className="flex items-center space-x-2">
              <Building2 className="h-6 w-6 text-sidebar-primary" />
              <span className="font-semibold text-sidebar-foreground">
                Document Generator
              </span>
            </div>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={onToggle}
            className="text-sidebar-foreground hover:bg-sidebar-accent"
          >
            {isOpen ? (
              <ChevronLeft className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
          </Button>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        {visibleItems.map((item) => {
          const isActive = location.pathname === item.href
          const Icon = item.icon

          return (
            <Link
              key={item.name}
              to={item.href}
              className={cn(
                'flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors',
                'hover:bg-sidebar-accent hover:text-sidebar-accent-foreground',
                isActive 
                  ? 'bg-sidebar-primary text-sidebar-primary-foreground' 
                  : 'text-sidebar-foreground'
              )}
            >
              <Icon className="h-5 w-5 flex-shrink-0" />
              {isOpen && (
                <span className="font-medium">
                  {item.name}
                </span>
              )}
            </Link>
          )
        })}
      </nav>

      {/* User Info */}
      {user && (
        <div className="p-4 border-t border-sidebar-border">
          <div className={cn(
            'flex items-center space-x-3',
            !isOpen && 'justify-center'
          )}>
            <div className="h-8 w-8 bg-sidebar-primary rounded-full flex items-center justify-center">
              <span className="text-sm font-medium text-sidebar-primary-foreground">
                {user.first_name?.[0]?.toUpperCase() || 'U'}
              </span>
            </div>
            {isOpen && (
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-sidebar-foreground truncate">
                  {user.first_name} {user.last_name}
                </p>
                <p className="text-xs text-sidebar-foreground/70 truncate">
                  {user.role}
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

