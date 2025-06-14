import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Settings, User, Building2, Palette, Shield } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/contexts/AuthContext'

export default function SettingsPage() {
  const { user } = useAuth()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Instellingen</h1>
        <p className="text-muted-foreground">
          Beheer uw account en systeem instellingen
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <User className="mr-2 h-5 w-5" />
              Profiel Instellingen
            </CardTitle>
            <CardDescription>
              Beheer uw persoonlijke gegevens
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm font-medium">Naam</p>
              <p className="text-sm text-muted-foreground">
                {user?.first_name} {user?.last_name}
              </p>
            </div>
            <div>
              <p className="text-sm font-medium">Email</p>
              <p className="text-sm text-muted-foreground">
                {user?.email}
              </p>
            </div>
            <div>
              <p className="text-sm font-medium">Rol</p>
              <p className="text-sm text-muted-foreground">
                {user?.role}
              </p>
            </div>
            <Button variant="outline" className="w-full">
              Profiel Bewerken
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Building2 className="mr-2 h-5 w-5" />
              Organisatie Instellingen
            </CardTitle>
            <CardDescription>
              Beheer organisatie gegevens
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-32 flex items-center justify-center border-2 border-dashed border-muted-foreground/25 rounded-lg">
              <div className="text-center">
                <Building2 className="h-8 w-8 text-muted-foreground mx-auto mb-1" />
                <p className="text-sm text-muted-foreground">
                  Organisatie instellingen
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Palette className="mr-2 h-5 w-5" />
              Weergave Instellingen
            </CardTitle>
            <CardDescription>
              Pas de interface aan uw voorkeur aan
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-32 flex items-center justify-center border-2 border-dashed border-muted-foreground/25 rounded-lg">
              <div className="text-center">
                <Palette className="h-8 w-8 text-muted-foreground mx-auto mb-1" />
                <p className="text-sm text-muted-foreground">
                  Theme en layout instellingen
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Shield className="mr-2 h-5 w-5" />
              Beveiliging
            </CardTitle>
            <CardDescription>
              Beheer uw beveiligingsinstellingen
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-32 flex items-center justify-center border-2 border-dashed border-muted-foreground/25 rounded-lg">
              <div className="text-center">
                <Shield className="h-8 w-8 text-muted-foreground mx-auto mb-1" />
                <p className="text-sm text-muted-foreground">
                  Wachtwoord en beveiliging
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Settings className="mr-2 h-5 w-5" />
            Systeem Instellingen
          </CardTitle>
          <CardDescription>
            Geavanceerde systeem configuratie (alleen voor beheerders)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-32 flex items-center justify-center border-2 border-dashed border-muted-foreground/25 rounded-lg">
            <div className="text-center">
              <Settings className="h-8 w-8 text-muted-foreground mx-auto mb-1" />
              <p className="text-sm text-muted-foreground">
                Systeem configuratie interface
              </p>
              <p className="text-xs text-muted-foreground">
                (Implementatie volgt in volgende fase)
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

