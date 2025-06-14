import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Users, Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'

export default function CustomersPage() {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Klanten</h1>
          <p className="text-muted-foreground">
            Beheer uw klanten en contactgegevens
          </p>
        </div>
        <Button>
          <Plus className="mr-2 h-4 w-4" />
          Nieuwe Klant
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Users className="mr-2 h-5 w-5" />
            Klanten Overzicht
          </CardTitle>
          <CardDescription>
            Klanten beheer functionaliteit wordt geïmplementeerd in de volgende fase
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center border-2 border-dashed border-muted-foreground/25 rounded-lg">
            <div className="text-center">
              <Users className="h-12 w-12 text-muted-foreground mx-auto mb-2" />
              <p className="text-muted-foreground">
                Klanten lijst en beheer interface
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

