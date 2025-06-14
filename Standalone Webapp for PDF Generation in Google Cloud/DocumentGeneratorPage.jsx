import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { 
  FileText, 
  Download, 
  Eye, 
  Plus, 
  AlertCircle,
  CheckCircle,
  Loader2
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { apiClient } from '@/services/apiClient'
import LoadingSpinner from '@/components/ui/LoadingSpinner'

const TEMPLATE_TYPES = {
  'offerte': 'Offerte',
  'factuur': 'Factuur',
  'factuur_gecombineerd': 'Factuur Gecombineerd',
  'werkbon': 'Werkbon'
}

export default function DocumentGeneratorPage() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [previewLoading, setPreviewLoading] = useState(false)
  const [templates, setTemplates] = useState([])
  const [customers, setCustomers] = useState([])
  const [orders, setOrders] = useState([])
  const [products, setProducts] = useState([])
  
  const [formData, setFormData] = useState({
    template_type: '',
    order_id: '',
    customer_data: {
      company_name: '',
      contact_person: '',
      email: '',
      phone: '',
      address: {
        street: '',
        postal_code: '',
        city: ''
      }
    },
    document_number: '',
    description: '',
    notes: '',
    items: []
  })
  
  const [preview, setPreview] = useState(null)
  const [validation, setValidation] = useState(null)
  const [generatedDocument, setGeneratedDocument] = useState(null)

  useEffect(() => {
    loadInitialData()
  }, [])

  const loadInitialData = async () => {
    try {
      setLoading(true)
      
      // Load templates, customers, orders, and products in parallel
      const [templatesRes, customersRes, ordersRes, productsRes] = await Promise.all([
        apiClient.get('/documents/templates'),
        apiClient.get('/customers'),
        apiClient.get('/orders'),
        apiClient.get('/products')
      ])
      
      setTemplates(templatesRes.data.templates || [])
      setCustomers(customersRes.data.customers || [])
      setOrders(ordersRes.data.orders || [])
      setProducts(productsRes.data.products || [])
      
    } catch (error) {
      console.error('Failed to load initial data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handleNestedInputChange = (parentField, field, value) => {
    setFormData(prev => ({
      ...prev,
      [parentField]: {
        ...prev[parentField],
        [field]: value
      }
    }))
  }

  const handleAddressChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      customer_data: {
        ...prev.customer_data,
        address: {
          ...prev.customer_data.address,
          [field]: value
        }
      }
    }))
  }

  const handleOrderSelect = (orderId) => {
    const selectedOrder = orders.find(order => order.id === orderId)
    if (selectedOrder) {
      setFormData(prev => ({
        ...prev,
        order_id: orderId,
        customer_data: selectedOrder.customer || prev.customer_data,
        items: selectedOrder.items || []
      }))
    }
  }

  const handleAddItem = () => {
    setFormData(prev => ({
      ...prev,
      items: [
        ...prev.items,
        {
          description: '',
          quantity: 1,
          unit: 'stuks',
          unit_price_excl_btw: 0,
          btw_percentage: 21,
          total_excl_btw: 0,
          total_incl_btw: 0,
          delivery_notes: ''
        }
      ]
    }))
  }

  const handleItemChange = (index, field, value) => {
    setFormData(prev => {
      const newItems = [...prev.items]
      newItems[index] = {
        ...newItems[index],
        [field]: value
      }
      
      // Recalculate totals if price or quantity changes
      if (field === 'quantity' || field === 'unit_price_excl_btw' || field === 'btw_percentage') {
        const item = newItems[index]
        const quantity = parseFloat(item.quantity) || 0
        const unitPrice = parseFloat(item.unit_price_excl_btw) || 0
        const btwPercentage = parseFloat(item.btw_percentage) || 0
        
        const totalExclBtw = quantity * unitPrice
        const btwAmount = totalExclBtw * (btwPercentage / 100)
        const totalInclBtw = totalExclBtw + btwAmount
        
        newItems[index] = {
          ...newItems[index],
          total_excl_btw: totalExclBtw,
          total_btw: btwAmount,
          total_incl_btw: totalInclBtw
        }
      }
      
      return {
        ...prev,
        items: newItems
      }
    })
  }

  const handleRemoveItem = (index) => {
    setFormData(prev => ({
      ...prev,
      items: prev.items.filter((_, i) => i !== index)
    }))
  }

  const handlePreview = async () => {
    try {
      setPreviewLoading(true)
      
      const response = await apiClient.post('/documents/generate/preview', formData)
      
      setPreview(response.data.document_data)
      setValidation(response.data.validation)
      
    } catch (error) {
      console.error('Preview failed:', error)
    } finally {
      setPreviewLoading(false)
    }
  }

  const handleGenerate = async () => {
    try {
      setLoading(true)
      
      const response = await apiClient.post('/documents/generate', formData)
      
      setGeneratedDocument(response.data.document)
      
      // Reset form
      setFormData({
        template_type: '',
        order_id: '',
        customer_data: {
          company_name: '',
          contact_person: '',
          email: '',
          phone: '',
          address: { street: '', postal_code: '', city: '' }
        },
        document_number: '',
        description: '',
        notes: '',
        items: []
      })
      setPreview(null)
      setValidation(null)
      
    } catch (error) {
      console.error('Document generation failed:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading && !templates.length) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner text="Laden..." />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Document Genereren</h1>
        <p className="text-muted-foreground">
          Genereer professionele documenten met uw sjablonen
        </p>
      </div>

      {generatedDocument && (
        <Alert>
          <CheckCircle className="h-4 w-4" />
          <AlertDescription>
            Document succesvol gegenereerd: {generatedDocument.document_number}
            <div className="mt-2 space-x-2">
              <Button size="sm" variant="outline" asChild>
                <a href={generatedDocument.pdf_url} target="_blank" rel="noopener noreferrer">
                  <Download className="mr-2 h-4 w-4" />
                  PDF Downloaden
                </a>
              </Button>
              <Button size="sm" variant="outline" onClick={() => navigate('/documents')}>
                <FileText className="mr-2 h-4 w-4" />
                Alle Documenten
              </Button>
            </div>
          </AlertDescription>
        </Alert>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Form */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Document Instellingen</CardTitle>
              <CardDescription>
                Selecteer sjabloon en vul basisgegevens in
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="template_type">Sjabloon Type</Label>
                <Select 
                  value={formData.template_type} 
                  onValueChange={(value) => handleInputChange('template_type', value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Selecteer sjabloon type" />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(TEMPLATE_TYPES).map(([key, label]) => (
                      <SelectItem key={key} value={key}>
                        {label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="order_id">Bestaande Opdracht (optioneel)</Label>
                <Select 
                  value={formData.order_id} 
                  onValueChange={handleOrderSelect}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Selecteer opdracht" />
                  </SelectTrigger>
                  <SelectContent>
                    {orders.map((order) => (
                      <SelectItem key={order.id} value={order.id}>
                        {order.order_number} - {order.customer?.company_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="document_number">Document Nummer</Label>
                <Input
                  id="document_number"
                  value={formData.document_number}
                  onChange={(e) => handleInputChange('document_number', e.target.value)}
                  placeholder="Laat leeg voor automatische generatie"
                />
              </div>

              <div>
                <Label htmlFor="description">Omschrijving</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                  placeholder="Document omschrijving"
                />
              </div>

              <div>
                <Label htmlFor="notes">Notities</Label>
                <Textarea
                  id="notes"
                  value={formData.notes}
                  onChange={(e) => handleInputChange('notes', e.target.value)}
                  placeholder="Extra notities"
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Klant Gegevens</CardTitle>
              <CardDescription>
                Klant informatie voor het document
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="company_name">Bedrijfsnaam</Label>
                <Input
                  id="company_name"
                  value={formData.customer_data.company_name}
                  onChange={(e) => handleNestedInputChange('customer_data', 'company_name', e.target.value)}
                  placeholder="Bedrijfsnaam"
                />
              </div>

              <div>
                <Label htmlFor="contact_person">Contactpersoon</Label>
                <Input
                  id="contact_person"
                  value={formData.customer_data.contact_person}
                  onChange={(e) => handleNestedInputChange('customer_data', 'contact_person', e.target.value)}
                  placeholder="Contactpersoon"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    value={formData.customer_data.email}
                    onChange={(e) => handleNestedInputChange('customer_data', 'email', e.target.value)}
                    placeholder="email@bedrijf.nl"
                  />
                </div>
                <div>
                  <Label htmlFor="phone">Telefoon</Label>
                  <Input
                    id="phone"
                    value={formData.customer_data.phone}
                    onChange={(e) => handleNestedInputChange('customer_data', 'phone', e.target.value)}
                    placeholder="06-12345678"
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="street">Adres</Label>
                <Input
                  id="street"
                  value={formData.customer_data.address.street}
                  onChange={(e) => handleAddressChange('street', e.target.value)}
                  placeholder="Straat en huisnummer"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="postal_code">Postcode</Label>
                  <Input
                    id="postal_code"
                    value={formData.customer_data.address.postal_code}
                    onChange={(e) => handleAddressChange('postal_code', e.target.value)}
                    placeholder="1234 AB"
                  />
                </div>
                <div>
                  <Label htmlFor="city">Plaats</Label>
                  <Input
                    id="city"
                    value={formData.customer_data.address.city}
                    onChange={(e) => handleAddressChange('city', e.target.value)}
                    placeholder="Plaats"
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                Producten/Diensten
                <Button size="sm" onClick={handleAddItem}>
                  <Plus className="mr-2 h-4 w-4" />
                  Item Toevoegen
                </Button>
              </CardTitle>
              <CardDescription>
                Voeg producten of diensten toe aan het document
              </CardDescription>
            </CardHeader>
            <CardContent>
              {formData.items.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  Geen items toegevoegd. Klik op "Item Toevoegen" om te beginnen.
                </div>
              ) : (
                <div className="space-y-4">
                  {formData.items.map((item, index) => (
                    <div key={index} className="border rounded-lg p-4 space-y-3">
                      <div className="flex justify-between items-start">
                        <h4 className="font-medium">Item {index + 1}</h4>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleRemoveItem(index)}
                        >
                          Verwijderen
                        </Button>
                      </div>
                      
                      <div>
                        <Label>Omschrijving</Label>
                        <Textarea
                          value={item.description}
                          onChange={(e) => handleItemChange(index, 'description', e.target.value)}
                          placeholder="Product/dienst omschrijving"
                        />
                      </div>
                      
                      <div className="grid grid-cols-3 gap-3">
                        <div>
                          <Label>Aantal</Label>
                          <Input
                            type="number"
                            value={item.quantity}
                            onChange={(e) => handleItemChange(index, 'quantity', e.target.value)}
                            min="0"
                            step="0.01"
                          />
                        </div>
                        <div>
                          <Label>Eenheid</Label>
                          <Input
                            value={item.unit}
                            onChange={(e) => handleItemChange(index, 'unit', e.target.value)}
                            placeholder="stuks"
                          />
                        </div>
                        <div>
                          <Label>Prijs excl. BTW</Label>
                          <Input
                            type="number"
                            value={item.unit_price_excl_btw}
                            onChange={(e) => handleItemChange(index, 'unit_price_excl_btw', e.target.value)}
                            min="0"
                            step="0.01"
                          />
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <Label>BTW %</Label>
                          <Input
                            type="number"
                            value={item.btw_percentage}
                            onChange={(e) => handleItemChange(index, 'btw_percentage', e.target.value)}
                            min="0"
                            max="100"
                          />
                        </div>
                        <div>
                          <Label>Totaal incl. BTW</Label>
                          <Input
                            value={`€ ${(item.total_incl_btw || 0).toFixed(2)}`}
                            disabled
                          />
                        </div>
                      </div>
                      
                      <div>
                        <Label>Notities</Label>
                        <Input
                          value={item.delivery_notes}
                          onChange={(e) => handleItemChange(index, 'delivery_notes', e.target.value)}
                          placeholder="Extra notities voor dit item"
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Preview and Actions */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Acties</CardTitle>
              <CardDescription>
                Bekijk preview en genereer document
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Button
                onClick={handlePreview}
                disabled={!formData.template_type || previewLoading}
                className="w-full"
                variant="outline"
              >
                {previewLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Preview Laden...
                  </>
                ) : (
                  <>
                    <Eye className="mr-2 h-4 w-4" />
                    Preview Bekijken
                  </>
                )}
              </Button>

              <Button
                onClick={handleGenerate}
                disabled={!formData.template_type || loading || (validation && !validation.is_valid)}
                className="w-full"
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Document Genereren...
                  </>
                ) : (
                  <>
                    <FileText className="mr-2 h-4 w-4" />
                    Document Genereren
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {validation && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  {validation.is_valid ? (
                    <CheckCircle className="mr-2 h-5 w-5 text-green-500" />
                  ) : (
                    <AlertCircle className="mr-2 h-5 w-5 text-red-500" />
                  )}
                  Validatie
                </CardTitle>
              </CardHeader>
              <CardContent>
                {validation.errors.length > 0 && (
                  <div className="space-y-2">
                    <h4 className="font-medium text-red-600">Fouten:</h4>
                    {validation.errors.map((error, index) => (
                      <div key={index} className="text-sm text-red-600">
                        • {error}
                      </div>
                    ))}
                  </div>
                )}
                
                {validation.warnings.length > 0 && (
                  <div className="space-y-2 mt-4">
                    <h4 className="font-medium text-yellow-600">Waarschuwingen:</h4>
                    {validation.warnings.map((warning, index) => (
                      <div key={index} className="text-sm text-yellow-600">
                        • {warning}
                      </div>
                    ))}
                  </div>
                )}
                
                {validation.is_valid && (
                  <div className="text-green-600 text-sm">
                    ✓ Alle gegevens zijn geldig voor document generatie
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {preview && (
            <Card>
              <CardHeader>
                <CardTitle>Preview Data</CardTitle>
                <CardDescription>
                  Data die gebruikt wordt voor document generatie
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 text-sm">
                  <div>
                    <strong>Klant:</strong> {preview.customer?.company_name}
                  </div>
                  <div>
                    <strong>Document:</strong> {preview.document_number}
                  </div>
                  <div>
                    <strong>Items:</strong> {preview.items?.length || 0}
                  </div>
                  {preview.totals && (
                    <div>
                      <strong>Totaal:</strong> € {preview.totals.total_incl_btw?.toFixed(2)}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}

