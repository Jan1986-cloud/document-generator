<<<<<<< HEAD
import { useState } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate, Link } from 'react-router-dom'
=======
import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
>>>>>>> cab5961336a072fa1190d0bb41a519aff2ec65c0
import { FileText, Users, BarChart3, Settings, Plus, Download, Eye, Edit } from 'lucide-react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Label } from '@/components/ui/label.jsx'
import { Textarea } from '@/components/ui/textarea.jsx'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx'
import { fetchApiInfo } from '@/lib/api.js'
import './App.css'

// Homepage Component
function HomePage() {
  const [apiInfo, setApiInfo] = useState(null)
  useEffect(() => {
    fetchApiInfo()
      .then(setApiInfo)
      .catch((err) => console.error('API error', err))
  }, [])
  const stats = [
    { title: 'Documenten Gegenereerd', value: '1,234', icon: FileText, color: 'text-blue-600' },
    { title: 'Actieve Klanten', value: '89', icon: Users, color: 'text-green-600' },
    { title: 'Templates Beschikbaar', value: '12', icon: BarChart3, color: 'text-purple-600' },
    { title: 'Deze Maand', value: '156', icon: Settings, color: 'text-orange-600' }
  ]

  const recentDocuments = [
    { id: 1, name: 'Offerte ABC Company', type: 'Offerte', date: '2024-06-28', status: 'Voltooid' },
    { id: 2, name: 'Contract XYZ B.V.', type: 'Contract', date: '2024-06-27', status: 'Concept' },
    { id: 3, name: 'Factuur #2024-001', type: 'Factuur', date: '2024-06-26', status: 'Verzonden' },
    { id: 4, name: 'Rapport Q2 2024', type: 'Rapport', date: '2024-06-25', status: 'Voltooid' }
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <FileText className="h-8 w-8 text-blue-600 mr-3" />
              <h1 className="text-2xl font-bold text-gray-900">Document Generator</h1>
            </div>
            <nav className="flex space-x-8">
              <a href="#" className="text-gray-500 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">Dashboard</a>
              <a href="#" className="text-gray-500 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">Templates</a>
              <a href="#" className="text-gray-500 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">Klanten</a>
              <a href="#" className="text-gray-500 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium">Instellingen</a>
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">Welkom bij Document Generator</h2>
          <p className="text-lg text-gray-600">Genereer professionele documenten met gemak en snelheid</p>
          {apiInfo && (
            <pre className="mt-4 bg-gray-100 p-4 text-sm rounded">
              {JSON.stringify(apiInfo, null, 2)}
            </pre>
          )}
        </div>

        {/* Quick Actions */}
        <div className="mb-8">
          <div className="flex flex-wrap gap-4">
            <Link to="/generate">
              <Button asChild className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 text-lg">
                <Plus className="h-5 w-5 mr-2" />
                Nieuw Document
              </Button>
            </Link>
            <Button variant="outline" className="px-6 py-3 text-lg">
              <FileText className="h-5 w-5 mr-2" />
              Templates Beheren
            </Button>
            <Button variant="outline" className="px-6 py-3 text-lg">
              <Users className="h-5 w-5 mr-2" />
              Klanten Beheren
            </Button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {stats.map((stat, index) => (
            <Card key={index} className="hover:shadow-lg transition-shadow">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-gray-600">
                  {stat.title}
                </CardTitle>
                <stat.icon className={`h-5 w-5 ${stat.color}`} />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-gray-900">{stat.value}</div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Recent Documents */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="text-xl font-semibold">Recente Documenten</CardTitle>
            <CardDescription>Je laatst gegenereerde documenten</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentDocuments.map((doc) => (
                <div key={doc.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50">
                  <div className="flex items-center space-x-4">
                    <FileText className="h-8 w-8 text-blue-600" />
                    <div>
                      <h3 className="font-medium text-gray-900">{doc.name}</h3>
                      <p className="text-sm text-gray-500">{doc.type} • {doc.date}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    <Badge variant={doc.status === 'Voltooid' ? 'default' : doc.status === 'Verzonden' ? 'secondary' : 'outline'}>
                      {doc.status}
                    </Badge>
                    <div className="flex space-x-2">
                      <Button variant="ghost" size="sm">
                        <Eye className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm">
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm">
                        <Download className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Features Section */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <FileText className="h-12 w-12 text-blue-600 mb-4" />
              <CardTitle>Professionele Templates</CardTitle>
              <CardDescription>
                Kies uit een uitgebreide collectie van professionele document templates
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <Users className="h-12 w-12 text-green-600 mb-4" />
              <CardTitle>Klantenbeheer</CardTitle>
              <CardDescription>
                Beheer je klantgegevens en genereer gepersonaliseerde documenten
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <BarChart3 className="h-12 w-12 text-purple-600 mb-4" />
              <CardTitle>Rapportage & Analytics</CardTitle>
              <CardDescription>
                Krijg inzicht in je document productie en klant activiteiten
              </CardDescription>
            </CardHeader>
          </Card>
        </div>
      </main>
    </div>
  )
}

// Document Generator Form Component
function DocumentGenerator() {
  const [formData, setFormData] = useState({
    documentType: '',
    clientName: '',
    clientEmail: '',
    clientAddress: '',
    projectTitle: '',
    projectDescription: '',
    amount: '',
    dueDate: '',
    additionalNotes: ''
  })

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    console.log('Form submitted:', formData)
    // Here you would typically send the data to your backend
    alert('Document wordt gegenereerd! (Demo functionaliteit)')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <FileText className="h-8 w-8 text-blue-600 mr-3" />
              <h1 className="text-2xl font-bold text-gray-900">Document Generator</h1>
            </div>
            <Button variant="outline" onClick={() => window.location.href = '/'}>
              ← Terug naar Dashboard
            </Button>
          </div>
        </div>
      </header>

      {/* Form Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">Nieuw Document Genereren</h2>
          <p className="text-lg text-gray-600">Vul de onderstaande gegevens in om een professioneel document te genereren</p>
        </div>

        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle className="text-xl">Document Informatie</CardTitle>
            <CardDescription>Voer de benodigde informatie in voor je document</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Document Type */}
              <div className="space-y-2">
                <Label htmlFor="documentType">Document Type</Label>
                <Select onValueChange={(value) => handleInputChange('documentType', value)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Selecteer document type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="offerte">Offerte</SelectItem>
                    <SelectItem value="factuur">Factuur</SelectItem>
                    <SelectItem value="contract">Contract</SelectItem>
                    <SelectItem value="rapport">Rapport</SelectItem>
                    <SelectItem value="brief">Zakelijke Brief</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Client Information */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label htmlFor="clientName">Klant Naam</Label>
                  <Input
                    id="clientName"
                    placeholder="Bijv. ABC Company B.V."
                    value={formData.clientName}
                    onChange={(e) => handleInputChange('clientName', e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="clientEmail">Klant Email</Label>
                  <Input
                    id="clientEmail"
                    type="email"
                    placeholder="contact@abccompany.nl"
                    value={formData.clientEmail}
                    onChange={(e) => handleInputChange('clientEmail', e.target.value)}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="clientAddress">Klant Adres</Label>
                <Textarea
                  id="clientAddress"
                  placeholder="Straatnaam 123&#10;1234 AB Stad"
                  value={formData.clientAddress}
                  onChange={(e) => handleInputChange('clientAddress', e.target.value)}
                  rows={3}
                />
              </div>

              {/* Project Information */}
              <div className="space-y-2">
                <Label htmlFor="projectTitle">Project Titel</Label>
                <Input
                  id="projectTitle"
                  placeholder="Bijv. Website Development Project"
                  value={formData.projectTitle}
                  onChange={(e) => handleInputChange('projectTitle', e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="projectDescription">Project Beschrijving</Label>
                <Textarea
                  id="projectDescription"
                  placeholder="Beschrijf het project in detail..."
                  value={formData.projectDescription}
                  onChange={(e) => handleInputChange('projectDescription', e.target.value)}
                  rows={4}
                />
              </div>

              {/* Financial Information */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label htmlFor="amount">Bedrag (€)</Label>
                  <Input
                    id="amount"
                    type="number"
                    placeholder="1500.00"
                    value={formData.amount}
                    onChange={(e) => handleInputChange('amount', e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="dueDate">Vervaldatum</Label>
                  <Input
                    id="dueDate"
                    type="date"
                    value={formData.dueDate}
                    onChange={(e) => handleInputChange('dueDate', e.target.value)}
                  />
                </div>
              </div>

              {/* Additional Notes */}
              <div className="space-y-2">
                <Label htmlFor="additionalNotes">Aanvullende Opmerkingen</Label>
                <Textarea
                  id="additionalNotes"
                  placeholder="Eventuele extra informatie of speciale instructies..."
                  value={formData.additionalNotes}
                  onChange={(e) => handleInputChange('additionalNotes', e.target.value)}
                  rows={3}
                />
              </div>

              {/* Submit Button */}
              <div className="flex justify-end space-x-4 pt-6">
                <Button type="button" variant="outline">
                  Opslaan als Concept
                </Button>
                <Button type="submit" className="bg-blue-600 hover:bg-blue-700">
                  <FileText className="h-4 w-4 mr-2" />
                  Document Genereren
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </main>
    </div>
  )
}

// Main App Component with Routing
function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/generate" element={<DocumentGenerator />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  )
}

export default App

