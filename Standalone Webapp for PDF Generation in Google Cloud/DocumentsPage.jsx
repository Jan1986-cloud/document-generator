import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { 
  FileText, 
  Plus, 
  Download, 
  Eye, 
  Trash2, 
  RefreshCw,
  Search,
  Filter
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { apiClient } from '@/services/apiClient'
import LoadingSpinner from '@/components/ui/LoadingSpinner'

const TEMPLATE_TYPES = {
  'offerte': 'Offerte',
  'factuur': 'Factuur',
  'factuur_gecombineerd': 'Factuur Gecombineerd',
  'werkbon': 'Werkbon'
}

export default function DocumentsPage() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [documents, setDocuments] = useState([])
  const [templates, setTemplates] = useState([])
  const [searchQuery, setSearchQuery] = useState('')
  const [templateFilter, setTemplateFilter] = useState('')
  const [pagination, setPagination] = useState({
    page: 1,
    per_page: 10,
    total: 0,
    pages: 0
  })

  useEffect(() => {
    loadDocuments()
    loadTemplates()
  }, [pagination.page, searchQuery, templateFilter])

  const loadDocuments = async () => {
    try {
      setLoading(true)
      
      const params = {
        page: pagination.page,
        per_page: pagination.per_page,
        search: searchQuery,
        template_type: templateFilter
      }
      
      const response = await apiClient.get('/documents', params)
      
      setDocuments(response.data.items || [])
      setPagination(prev => ({
        ...prev,
        total: response.data.total || 0,
        pages: response.data.pages || 0
      }))
      
    } catch (error) {
      console.error('Failed to load documents:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadTemplates = async () => {
    try {
      const response = await apiClient.get('/documents/templates')
      setTemplates(response.data.templates || [])
    } catch (error) {
      console.error('Failed to load templates:', error)
    }
  }

  const handleSearch = (query) => {
    setSearchQuery(query)
    setPagination(prev => ({ ...prev, page: 1 }))
  }

  const handleFilterChange = (filter) => {
    setTemplateFilter(filter)
    setPagination(prev => ({ ...prev, page: 1 }))
  }

  const handleDeleteDocument = async (documentId) => {
    if (!confirm('Weet u zeker dat u dit document wilt verwijderen?')) {
      return
    }

    try {
      await apiClient.delete(`/documents/${documentId}`)
      loadDocuments() // Reload the list
    } catch (error) {
      console.error('Failed to delete document:', error)
    }
  }

  const handleRegenerateDocument = async (documentId) => {
    try {
      await apiClient.post(`/documents/${documentId}/regenerate`)
      loadDocuments() // Reload the list
    } catch (error) {
      console.error('Failed to regenerate document:', error)
    }
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('nl-NL', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getTemplateTypeBadge = (templateType) => {
    const colors = {
      'offerte': 'bg-blue-100 text-blue-800',
      'factuur': 'bg-green-100 text-green-800',
      'factuur_gecombineerd': 'bg-purple-100 text-purple-800',
      'werkbon': 'bg-orange-100 text-orange-800'
    }
    
    return (
      <Badge className={colors[templateType] || 'bg-gray-100 text-gray-800'}>
        {TEMPLATE_TYPES[templateType] || templateType}
      </Badge>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Documenten</h1>
          <p className="text-muted-foreground">
            Genereer en beheer uw documenten
          </p>
        </div>
        <Button onClick={() => navigate('/documents/generate')}>
          <Plus className="mr-2 h-4 w-4" />
          Document Genereren
        </Button>
      </div>

      {/* Templates Overview */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {Object.entries(TEMPLATE_TYPES).map(([key, label]) => {
          const template = templates.find(t => t.type === key)
          return (
            <Card key={key}>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium flex items-center justify-between">
                  {label}
                  <FileText className="h-4 w-4 text-muted-foreground" />
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <Button
                    size="sm"
                    className="w-full"
                    onClick={() => navigate('/documents/generate', { state: { templateType: key } })}
                  >
                    <Plus className="mr-2 h-3 w-3" />
                    Genereren
                  </Button>
                  {template && (
                    <Button
                      size="sm"
                      variant="outline"
                      className="w-full"
                      asChild
                    >
                      <a href={`https://docs.google.com/document/d/${template.google_doc_id}`} target="_blank" rel="noopener noreferrer">
                        <Eye className="mr-2 h-3 w-3" />
                        Sjabloon Bekijken
                      </a>
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Documents List */}
      <Card>
        <CardHeader>
          <CardTitle>Gegenereerde Documenten</CardTitle>
          <CardDescription>
            Overzicht van alle gegenereerde documenten
          </CardDescription>
          
          {/* Search and Filter */}
          <div className="flex space-x-4 mt-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Zoeken op document nummer of bestandsnaam..."
                  value={searchQuery}
                  onChange={(e) => handleSearch(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <Select value={templateFilter} onValueChange={handleFilterChange}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filter op type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">Alle types</SelectItem>
                {Object.entries(TEMPLATE_TYPES).map(([key, label]) => (
                  <SelectItem key={key} value={key}>
                    {label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center h-32">
              <LoadingSpinner text="Documenten laden..." />
            </div>
          ) : documents.length === 0 ? (
            <div className="text-center py-8">
              <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-medium mb-2">Geen documenten gevonden</h3>
              <p className="text-muted-foreground mb-4">
                {searchQuery || templateFilter 
                  ? 'Geen documenten gevonden met de huidige filters.'
                  : 'U heeft nog geen documenten gegenereerd.'
                }
              </p>
              <Button onClick={() => navigate('/documents/generate')}>
                <Plus className="mr-2 h-4 w-4" />
                Eerste Document Genereren
              </Button>
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Document Nummer</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Klant</TableHead>
                    <TableHead>Aangemaakt</TableHead>
                    <TableHead>Acties</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {documents.map((document) => (
                    <TableRow key={document.id}>
                      <TableCell className="font-medium">
                        {document.document_number}
                      </TableCell>
                      <TableCell>
                        {getTemplateTypeBadge(document.template_type)}
                      </TableCell>
                      <TableCell>
                        {document.customer?.company_name || 'Onbekend'}
                      </TableCell>
                      <TableCell>
                        {formatDate(document.created_at)}
                      </TableCell>
                      <TableCell>
                        <div className="flex space-x-2">
                          <Button
                            size="sm"
                            variant="outline"
                            asChild
                          >
                            <a href={document.pdf_url} target="_blank" rel="noopener noreferrer">
                              <Download className="h-3 w-3" />
                            </a>
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            asChild
                          >
                            <a href={`https://docs.google.com/document/d/${document.google_doc_id}`} target="_blank" rel="noopener noreferrer">
                              <Eye className="h-3 w-3" />
                            </a>
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleRegenerateDocument(document.id)}
                          >
                            <RefreshCw className="h-3 w-3" />
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleDeleteDocument(document.id)}
                          >
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* Pagination */}
              {pagination.pages > 1 && (
                <div className="flex items-center justify-between mt-4">
                  <div className="text-sm text-muted-foreground">
                    Pagina {pagination.page} van {pagination.pages} ({pagination.total} documenten)
                  </div>
                  <div className="flex space-x-2">
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={pagination.page <= 1}
                      onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
                    >
                      Vorige
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={pagination.page >= pagination.pages}
                      onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
                    >
                      Volgende
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

