'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent } from "@/components/ui/card"
import { FileText, FileSpreadsheet, Presentation, File, Image as ImageIcon, Download, Eye, Shield, LogOut } from "lucide-react"

export function Dashboard() {
  const [files, setFiles] = useState<{ [key: string]: File[] }>({
    pdf: [],
    doc: [],
    ppt: [],
    xls: [],
    image: []
  })
  const [downloadLinks, setDownloadLinks] = useState<string[]>([])
  const router = useRouter()

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) {
      router.push('/signin')
    }
  }, [router])

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>, fileType: string) => {
    const uploadedFiles = Array.from(event.target.files || [])
    setFiles(prev => ({ ...prev, [fileType]: [...prev[fileType], ...uploadedFiles] }))
  }

  const getFileNameFromDisposition = (disposition: string | null): string | null => {
    if (!disposition) return null
    // Example: Content-Disposition: attachment; filename="processed_file.docx"
    const fileNameMatch = disposition.match(/filename="?([^"]+)"?/)
    return fileNameMatch && fileNameMatch[1] ? fileNameMatch[1] : null
  }

  const handleUploadAll = async () => {
    const formData = new FormData()
    Object.values(files).flat().forEach(file => {
      formData.append('file', file)
    })

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_FAST_API_URL}/upload`, {
        method: 'POST',
        body: formData,
        headers: {
          'Accept': 'application/json',
          // Remove Content-Type header to let the browser set it with the correct boundary for FormData
          'Origin': window.location.origin,
        },
        credentials: 'include', // Include cookies if needed
      })

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
      }

      // Check the Content-Type header to decide how to parse the response
      const contentType = response.headers.get('Content-Type') || ''
      if (contentType.toLowerCase().includes('application/json')) {
        // Handle unexpected JSON response (e.g. error handling).
        const data = await response.json()
        console.error('Error:', data.error)
      } else {
        // Process the response as a binary file.
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)

        // Try to extract a dynamic filename from the Content-Disposition header.
        const disposition = response.headers.get('Content-Disposition')
        let fileName = getFileNameFromDisposition(disposition)
        if (!fileName) {
          // Fallback based on content type
          if (contentType.includes('pdf')) {
            fileName = 'processed_file.pdf'
          } else if (contentType.includes('vnd.openxmlformats-officedocument.wordprocessingml.document') || contentType.includes('msword')) {
            fileName = 'processed_file.doc'
          } else if (contentType.includes('vnd.openxmlformats-officedocument.spreadsheetml.sheet') || contentType.includes('excel')) {
            fileName = 'processed_file.xlsx'
          } else if (contentType.includes('vnd.openxmlformats-officedocument.presentationml.presentation')) {
            fileName = 'processed_file.ppt'
          } else {
            fileName = 'processed_file'
          }
        }

        // Create and trigger download.
        const link = document.createElement('a')
        link.href = url
        link.download = fileName
        document.body.appendChild(link)
        link.click()
        link.remove()
        // Optionally store the link to display a download button:
        setDownloadLinks([url])
      }
    } catch (error) {
      console.error('Error uploading file:', error instanceof Error ? error.message : 'An unknown error occurred');
      // You might want to show this error to the user through a toast notification
    }
  }

  const renderFileList = (fileType: string) => (
    <div className="mt-4 space-y-2">
      {files[fileType].map((file, index) => (
        <div key={index} className="flex items-center space-x-2 bg-blue-50 p-2 rounded">
          {fileType === 'pdf' && <FileText className="h-5 w-5 text-blue-500" />}
          {fileType === 'doc' && <File className="h-5 w-5 text-blue-500" />}
          {fileType === 'ppt' && <Presentation className="h-5 w-5 text-blue-500" />}
          {fileType === 'xls' && <FileSpreadsheet className="h-5 w-5 text-blue-500" />}
          {fileType === 'image' && <ImageIcon className="h-5 w-5 text-blue-500" />}
          <span className="text-blue-600">{file.name}</span>
        </div>
      ))}
    </div>
  )

  return (
    <div className="min-h-screen bg-white flex">
      {/* Sidebar */}
      <div className="w-64 bg-blue-600 text-white p-6 flex flex-col">
        <div className="flex items-center mb-8">
          <Shield className="h-8 w-8 mr-2" />
          <h1 className="text-2xl font-bold">Urushya</h1>
        </div>
        <nav className="flex-grow">
          <ul className="space-y-2">
            <li><Button variant="ghost" className="w-full justify-start text-white hover:bg-blue-700">Dashboard</Button></li>
            <li><Button variant="ghost" className="w-full justify-start text-white hover:bg-blue-700">History</Button></li>
            <li><Button variant="ghost" className="w-full justify-start text-white hover:bg-blue-700">Settings</Button></li>
          </ul>
        </nav>
        <div>
          <Button className="w-full bg-blue-500 hover:bg-blue-400 text-white">
            <LogOut className="mr-2 h-4 w-4" /> Logout
          </Button>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-grow bg-gray-50">
        <header className="bg-white shadow-sm p-4 flex justify-between items-center">
          <h2 className="text-2xl font-bold text-blue-600">Document Processing</h2>
          <Button className="bg-blue-600 hover:bg-blue-700 text-white">
            <Eye className="mr-2 h-5 w-5" />
            Preview
          </Button>
        </header>

        <main className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              { type: 'pdf', label: 'PDF Files', accept: '.pdf', icon: FileText },
              { type: 'doc', label: 'Word Documents', accept: '.doc,.docx', icon: File },
              { type: 'ppt', label: 'Presentations', accept: '.ppt,.pptx', icon: Presentation },
              { type: 'xls', label: 'Spreadsheets', accept: '.xls,.xlsx', icon: FileSpreadsheet },
              { type: 'image', label: 'Images', accept: 'image/*', icon: ImageIcon },
            ].map((fileType) => (
              <Card key={fileType.type} className="border-blue-200">
                <CardContent className="p-6">
                  <Label htmlFor={`${fileType.type}-upload`} className="text-lg font-semibold text-blue-600 mb-2 block">
                    <fileType.icon className="inline-block mr-2 h-5 w-5" />
                    {fileType.label}
                  </Label>
                  <Input
                    id={`${fileType.type}-upload`}
                    type="file"
                    multiple
                    accept={fileType.accept}
                    onChange={(e) => handleFileUpload(e, fileType.type)}
                    className="border-blue-300 focus:border-blue-500"
                  />
                  {renderFileList(fileType.type)}
                </CardContent>
              </Card>
            ))}
          </div>

          <div className="mt-8 flex justify-center">
            <Button
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 text-lg"
              onClick={handleUploadAll}
              disabled={Object.values(files).flat().length === 0}
            >
              <Download className="mr-2 h-5 w-5" />
              Upload and Process All
            </Button>
          </div>

          <div className="mt-8 flex justify-center">
            {downloadLinks.map((link, index) => (
              <a
                key={index}
                href={link}
                download
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 text-lg"
              >
                <Download className="mr-2 h-5 w-5" />
                Download Processed File {index + 1}
              </a>
            ))}
          </div>
        </main>
      </div>
    </div>
  )
}