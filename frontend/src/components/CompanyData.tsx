import { useRef, useState } from 'react'
import './CompanyData.css'

type CompanyDetails = {
  companyName: string
  industry: string
  description: string
  departments: string
  policies: string
}

type UploadedFile = {
  id: string
  name: string
  size: number
  type: string
}

const DETAILS_KEY = 'companyBrainDetails'
const FILES_KEY = 'companyBrainUploadedFiles'
const MAX_FILE_SIZE = 10 * 1024 * 1024

const emptyDetails: CompanyDetails = {
  companyName: '',
  industry: '',
  description: '',
  departments: '',
  policies: '',
}

const loadDetails = (): CompanyDetails => {
  try {
    const saved = localStorage.getItem(DETAILS_KEY)
    return saved ? { ...emptyDetails, ...JSON.parse(saved) } : emptyDetails
  } catch {
    return emptyDetails
  }
}

const loadFiles = (): UploadedFile[] => {
  try {
    const saved = localStorage.getItem(FILES_KEY)
    const parsed = saved ? JSON.parse(saved) : []
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

function CompanyData() {
  const [details, setDetails] = useState<CompanyDetails>(loadDetails)
  const [files, setFiles] = useState<UploadedFile[]>(loadFiles)
  const [notice, setNotice] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const updateField = (
    field: keyof CompanyDetails,
    value: string
  ) => {
    setDetails((previous) => ({
      ...previous,
      [field]: value,
    }))
  }

  const saveDetails = () => {
    try {
      localStorage.setItem(DETAILS_KEY, JSON.stringify(details))
      setNotice('Company details saved successfully.')
    } catch {
      setNotice('Could not save details in this browser.')
    }
  }

  const addFiles = (selectedFiles: FileList | null) => {
    if (!selectedFiles) return

    const acceptedFiles: UploadedFile[] = []
    const errors: string[] = []

    Array.from(selectedFiles).forEach((file) => {
      const extension = file.name.split('.').pop()?.toLowerCase() ?? ''
      const allowed = [
        'pdf', 'doc', 'docx', 'xls', 'xlsx', 'csv', 'txt',
      ].includes(extension)

      if (!allowed) {
        errors.push(`${file.name}: unsupported file type`)
        return
      }

      if (file.size > MAX_FILE_SIZE) {
        errors.push(`${file.name}: larger than 10 MB`)
        return
      }

      acceptedFiles.push({
        id: `${file.name}-${file.size}-${Date.now()}-${Math.random()}`,
        name: file.name,
        size: file.size,
        type: file.type || extension.toUpperCase(),
      })
    })

    const nextFiles = [...files, ...acceptedFiles]
    const uniqueFiles = nextFiles.filter(
      (file, index, all) =>
        all.findIndex((item) => item.id === file.id) === index
    )

    try {
      localStorage.setItem(FILES_KEY, JSON.stringify(uniqueFiles))
      setFiles(uniqueFiles)

      if (errors.length) {
        setNotice(`Some files were skipped: ${errors.join('; ')}`)
      } else if (acceptedFiles.length) {
        setNotice(
          'File names added. The actual file contents are not stored yet.'
        )
      }
    } catch {
      setNotice('Could not save the file list in this browser.')
    }
  }

  const removeFile = (id: string) => {
    const nextFiles = files.filter((file) => file.id !== id)

    try {
      localStorage.setItem(FILES_KEY, JSON.stringify(nextFiles))
      setFiles(nextFiles)
      setNotice('File removed from the list.')
    } catch {
      setNotice('Could not update the file list.')
    }
  }

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) {
      return `${(bytes / 1024).toFixed(1)} KB`
    }
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <main className="company-data-page">
      <div className="company-data-heading">
        <div>
          <p className="company-data-eyebrow">COMPANY KNOWLEDGE</p>
          <h2>Company Data</h2>
          <p>
            Add your company information and keep your document list
            organised in one place.
          </p>
        </div>
      </div>

      <section className="company-data-card">
        <h3>Company details</h3>
        <p className="company-data-description">
          Enter the basic information you want to keep with your project.
        </p>

        <div className="company-data-form">
          <label>
            Company name
            <input
              value={details.companyName}
              onChange={(event) =>
                updateField('companyName', event.target.value)
              }
              placeholder="Enter your company name"
            />
          </label>

          <label>
            Industry
            <input
              value={details.industry}
              onChange={(event) =>
                updateField('industry', event.target.value)
              }
              placeholder="e.g. Retail, Manufacturing, Technology"
            />
          </label>

          <label className="company-data-full-width">
            Company description
            <textarea
              value={details.description}
              onChange={(event) =>
                updateField('description', event.target.value)
              }
              placeholder="Describe what your company does"
              rows={4}
            />
          </label>

          <label>
            Departments
            <textarea
              value={details.departments}
              onChange={(event) =>
                updateField('departments', event.target.value)
              }
              placeholder="e.g. Sales, HR, Finance"
              rows={3}
            />
          </label>

          <label>
            Policies and processes
            <textarea
              value={details.policies}
              onChange={(event) =>
                updateField('policies', event.target.value)
              }
              placeholder="Add key policies or processes"
              rows={3}
            />
          </label>
        </div>

        <div className="company-data-actions">
          <button
            className="company-data-primary"
            onClick={saveDetails}
          >
            Save company details
          </button>
        </div>
      </section>

      <section className="company-data-card">
        <h3>Company documents</h3>
        <p className="company-data-description">
          Choose PDF, Word, Excel, CSV, or text files up to 10 MB each.
        </p>

        <button
          type="button"
          className="company-data-dropzone"
          onClick={() => fileInputRef.current?.click()}
        >
          <span className="company-data-upload-icon">↑</span>
          <strong>Select documents</strong>
          <span>Click here to choose files from your computer</span>
          <span className="company-data-file-types">
            PDF · DOC · DOCX · XLS · XLSX · CSV · TXT
          </span>
        </button>

        <input
          ref={fileInputRef}
          className="company-data-hidden-input"
          type="file"
          multiple
          accept=".pdf,.doc,.docx,.xls,.xlsx,.csv,.txt"
          onChange={(event) => {
            addFiles(event.target.files)
            event.target.value = ''
          }}
        />

        {files.length > 0 ? (
          <div className="company-data-file-list">
            <div className="company-data-file-list-heading">
              <strong>Selected documents</strong>
              <span>{files.length} file{files.length === 1 ? '' : 's'}</span>
            </div>

            {files.map((file) => (
              <div className="company-data-file" key={file.id}>
                <span className="company-data-file-icon">FILE</span>
                <div className="company-data-file-info">
                  <strong>{file.name}</strong>
                  <span>{formatSize(file.size)}</span>
                </div>
                <button
                  type="button"
                  className="company-data-remove"
                  onClick={() => removeFile(file.id)}
                  aria-label={`Remove ${file.name}`}
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        ) : (
          <p className="company-data-empty">
            No documents added yet.
          </p>
        )}

        <p className="company-data-note">
          Prototype note: this currently saves document names only in your
          browser. It does not upload, read, or analyse the actual documents.
        </p>
      </section>

      {notice && (
        <p className="company-data-notice" role="status">
          {notice}
        </p>
      )}
    </main>
  )
}

export default CompanyData
