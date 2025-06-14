import { useState, useEffect } from 'react'
import { 
  Users, 
  Package, 
  ShoppingCart, 
  FileText,
  TrendingUp,
  Calendar,
  Clock,
  Euro
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import LoadingSpinner from '@/components/ui/LoadingSpinner'
import { useAuth } from '@/contexts/AuthContext'

// Mock data - replace with real API calls
const mockStats = {
  overview: {
    customers: 156,
    products: 89,
    orders: 234,
    documents: 567
  },
  recent_orders: [
    {
      id: 1,
      order_number: 'ORD-2024-0001',
      customer: { company_name: 'ABC Bouw BV' },
      total_incl_btw: 2450.00,
      status: 'confirmed',
      created_at: '2024-01-15T10:30:00Z'
    },
    {
      id: 2,
      order_number: 'ORD-2024-0002',
      customer: { company_name: 'XYZ Installaties' },
      total_incl_btw: 1890.50,
      status: 'in_progress',
      created_at: '2024-01-14T14:20:00Z'
    }
  ],
  monthly_revenue: [
    { month: '2024-01', revenue: 15420.50 },
    { month: '2024-02', revenue: 18750.25 },
    { month: '2024-03', revenue: 22100.75 }
  ]
}

function StatCard({ title, value, icon: Icon, description, trend }) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">
          {title}
        </CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {description && (
          <p className="text-xs text-muted-foreground">
            {description}
          </p>
        )}
        {trend && (
          <div className="flex items-center pt-1">
            <TrendingUp className="h-3 w-3 text-green-500 mr-1" />
            <span className="text-xs text-green-500">
              {trend}
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function RecentOrdersWidget({ orders }) {
  const getStatusBadge = (status) => {
    const statusConfig = {
      draft: { label: 'Concept', variant: 'secondary' },
      confirmed: { label: 'Bevestigd', variant: 'default' },
      in_progress: { label: 'In uitvoering', variant: 'default' },
      completed: { label: 'Voltooid', variant: 'default' },
      cancelled: { label: 'Geannuleerd', variant: 'destructive' }
    }
    
    const config = statusConfig[status] || { label: status, variant: 'secondary' }
    return <Badge variant={config.variant}>{config.label}</Badge>
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('nl-NL', {
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <Card className="col-span-2">
      <CardHeader>
        <CardTitle>Recente Opdrachten</CardTitle>
        <CardDescription>
          Laatste opdrachten in het systeem
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {orders.map((order) => (
            <div key={order.id} className="flex items-center justify-between p-3 border rounded-lg">
              <div className="flex-1">
                <div className="flex items-center space-x-2">
                  <span className="font-medium">{order.order_number}</span>
                  {getStatusBadge(order.status)}
                </div>
                <p className="text-sm text-muted-foreground">
                  {order.customer.company_name}
                </p>
                <p className="text-xs text-muted-foreground flex items-center">
                  <Clock className="h-3 w-3 mr-1" />
                  {formatDate(order.created_at)}
                </p>
              </div>
              <div className="text-right">
                <p className="font-medium">
                  €{order.total_incl_btw.toFixed(2)}
                </p>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-4">
          <Button variant="outline" className="w-full">
            Alle opdrachten bekijken
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

function QuickActionsWidget() {
  const quickActions = [
    {
      title: 'Nieuwe Opdracht',
      description: 'Maak een nieuwe opdracht aan',
      icon: ShoppingCart,
      href: '/orders/new'
    },
    {
      title: 'Klant Toevoegen',
      description: 'Voeg een nieuwe klant toe',
      icon: Users,
      href: '/customers/new'
    },
    {
      title: 'Product Toevoegen',
      description: 'Voeg een nieuw product toe',
      icon: Package,
      href: '/products/new'
    },
    {
      title: 'Document Genereren',
      description: 'Genereer een nieuw document',
      icon: FileText,
      href: '/documents/generate'
    }
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle>Snelle Acties</CardTitle>
        <CardDescription>
          Veelgebruikte functies
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-3">
          {quickActions.map((action) => (
            <Button
              key={action.title}
              variant="outline"
              className="h-auto p-3 flex flex-col items-center space-y-2"
              onClick={() => {
                // TODO: Navigate to action.href
                console.log('Navigate to:', action.href)
              }}
            >
              <action.icon className="h-5 w-5" />
              <div className="text-center">
                <div className="text-xs font-medium">{action.title}</div>
              </div>
            </Button>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

export default function DashboardPage() {
  const { user } = useAuth()
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Simulate API call
    const loadDashboardData = async () => {
      try {
        // TODO: Replace with real API call
        await new Promise(resolve => setTimeout(resolve, 1000))
        setStats(mockStats)
      } catch (error) {
        console.error('Failed to load dashboard data:', error)
      } finally {
        setLoading(false)
      }
    }

    loadDashboardData()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner text="Dashboard laden..." />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">
          Welkom terug, {user?.first_name}!
        </h1>
        <p className="text-muted-foreground">
          Hier is een overzicht van uw bedrijfsactiviteiten.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Klanten"
          value={stats?.overview.customers || 0}
          icon={Users}
          description="Actieve klanten"
          trend="+12% deze maand"
        />
        <StatCard
          title="Producten"
          value={stats?.overview.products || 0}
          icon={Package}
          description="Beschikbare producten"
        />
        <StatCard
          title="Opdrachten"
          value={stats?.overview.orders || 0}
          icon={ShoppingCart}
          description="Totaal aantal opdrachten"
          trend="+8% deze maand"
        />
        <StatCard
          title="Documenten"
          value={stats?.overview.documents || 0}
          icon={FileText}
          description="Gegenereerde documenten"
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid gap-6 md:grid-cols-3">
        <RecentOrdersWidget orders={stats?.recent_orders || []} />
        <QuickActionsWidget />
      </div>

      {/* Revenue Chart Placeholder */}
      <Card>
        <CardHeader>
          <CardTitle>Omzet Overzicht</CardTitle>
          <CardDescription>
            Maandelijkse omzet van de afgelopen periode
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center border-2 border-dashed border-muted-foreground/25 rounded-lg">
            <div className="text-center">
              <TrendingUp className="h-12 w-12 text-muted-foreground mx-auto mb-2" />
              <p className="text-muted-foreground">
                Omzet grafiek wordt hier weergegeven
              </p>
              <p className="text-sm text-muted-foreground">
                (Implementatie volgt in volgende fase)
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

