/**
 * Report Modal - Pool Scout Pro
 * Handles detailed facility and inspection information with management editing.
 */

class ReportModal {
    constructor() {
        this.editMode = false;
        this.currentFacilityData = null;
        this.managementCompanies = [];
    }

    async show(index) {
        const currentResults = window.searchService.getCurrentResults();
        const reportData = currentResults[index];

        if (!reportData) return;

        // Store current data and index for editing
        this.currentFacilityData = { ...reportData, index: index };

        // Close any existing modal
        this.close();

        // Load management companies for dropdown
        await this.loadManagementCompanies();

        const modalHtml = this._buildModalHtml(reportData);
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Add event listener to close modal on overlay click
        const overlay = document.getElementById('report-modal-overlay');
        if (overlay) {
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) {
                    this.close();
                }
            });
        }
    }

    close() {
        const existingModal = document.getElementById('report-modal-overlay');
        if (existingModal) {
            existingModal.remove();
        }
        this.editMode = false;
        this.currentFacilityData = null;
    }

    async loadManagementCompanies() {
        try {
            const response = await fetch('/api/v1/management-companies');
            const data = await response.json();
            if (data.success) {
                this.managementCompanies = data.companies || [];
            } else {
                console.warn('Failed to load management companies:', data.message);
                this.managementCompanies = [];
            }
        } catch (error) {
            console.error('Error loading management companies:', error);
            this.managementCompanies = [];
        }
    }

    toggleEditMode() {
        this.editMode = !this.editMode;
        if (this.currentFacilityData) {
            this.refreshModal();
        }
    }

    refreshModal() {
        const modalContent = document.querySelector('#report-modal-overlay .modal-content');
        if (modalContent) {
            try {
                modalContent.innerHTML = this._buildModalContent(this.currentFacilityData);
            } catch (error) {
                console.error('Error refreshing modal content:', error);
                // Fallback to non-edit mode if edit content fails
                this.editMode = false;
                modalContent.innerHTML = this._buildModalContent(this.currentFacilityData);
            }
        }
    }

    async saveManagement() {
        const facilityId = this.currentFacilityData.facility?.id || this.currentFacilityData.id;
        const sapphireManaged = document.getElementById('sapphire-managed-checkbox')?.checked || false;
        const managementCompany = document.getElementById('management-company-input')?.value?.trim() || '';

        if (!facilityId) {
            this.showMessage('Error: Facility ID not found', 'error');
            return;
        }

        try {
            const response = await fetch(`/api/v1/facilities/${facilityId}/management`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    sapphire_managed: sapphireManaged,
                    management_company: managementCompany
                })
            });

            const result = await response.json();
            if (result.success) {
                // Update local data
                if (this.currentFacilityData.facility) {
                    this.currentFacilityData.facility.sapphire_managed = sapphireManaged;
                    this.currentFacilityData.facility.management_company = managementCompany;
                } else {
                    this.currentFacilityData.sapphire_managed = sapphireManaged;
                    this.currentFacilityData.management_company = managementCompany;
                }
                
                // If new company was added, reload companies list
                if (managementCompany && !this.managementCompanies.includes(managementCompany)) {
                    await this.loadManagementCompanies();
                }
                
                this.editMode = false;
                this.refreshModal();
                
                this.showMessage('Management information saved successfully', 'success');
            } else {
                this.showMessage(result.message || 'Error saving management information', 'error');
            }
        } catch (error) {
            console.error('Error saving management:', error);
            this.showMessage('Error saving management information', 'error');
        }
    }

    showMessage(message, type) {
        const messageEl = document.createElement('div');
        messageEl.style.cssText = `
            position: fixed; top: 20px; right: 20px; z-index: 2000;
            padding: 12px 20px; border-radius: 6px; font-size: 14px;
            background: ${type === 'success' ? '#10b981' : '#ef4444'};
            color: white; box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        `;
        messageEl.textContent = message;
        document.body.appendChild(messageEl);
        
        setTimeout(() => messageEl.remove(), 3000);
    }

    _buildModalHtml(data) {
        return `
            <div id="report-modal-overlay" class="modal-overlay" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000; display: flex; align-items: center; justify-content: center;">
                <div class="modal-content" style="background: white; border-radius: 12px; max-width: 800px; max-height: 85vh; overflow-y: auto; margin: 20px; box-shadow: 0 8px 32px rgba(0,0,0,0.3);">
                    ${this._buildModalContent(data)}
                </div>
            </div>
        `;
    }

    _buildModalContent(data) {
        const facility = data.facility || data;
        const violationCount = data.violations ? data.violations.length : 0;
        const sapphireManaged = facility.sapphire_managed || false;
        const managementCompany = facility.management_company || '';

        const managementSection = this.editMode ? this._buildEditSection(sapphireManaged, managementCompany) : this._buildReadOnlySection(sapphireManaged, managementCompany);

        return `
            <div class="modal-header" style="padding: 20px; border-bottom: 1px solid #e5e7eb; display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; background: white; border-radius: 12px 12px 0 0;">
                <div>
                    <h2 style="margin: 0; color: #1f2937; font-size: 20px;">${this._escape(facility.name)}</h2>
                    <p style="margin: 4px 0 0 0; color: #6b7280; font-size: 14px;">${this._escape(facility.street_address)}, ${this._escape(facility.city)}</p>
                </div>
                <div style="display: flex; gap: 10px; align-items: center;">
                    <button onclick="window.reportModal.toggleEditMode()" style="background: #3b82f6; color: white; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 12px;">
                        ${this.editMode ? 'Cancel' : 'Edit'}
                    </button>
                    <button onclick="window.reportModal.close()" style="border: none; background: none; font-size: 24px; color: #6b7280; cursor: pointer; padding: 4px;">&times;</button>
                </div>
            </div>
            
            <div class="modal-body" style="padding: 20px;">
                ${managementSection}

                <div class="info-section" style="margin-bottom: 24px;">
                    <h3 style="margin: 0 0 12px 0; color: #1f2937; font-size: 16px; border-bottom: 2px solid #e5e7eb; padding-bottom: 4px;">Facility Information</h3>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; font-size: 14px;">
                        <div><strong>Name:</strong> ${this._escape(facility.name)}</div>
                        <div><strong>Program ID:</strong> ${this._escape(facility.program_identifier)}</div>
                        <div><strong>Address:</strong> ${this._escape(facility.street_address)}</div>
                        <div><strong>City:</strong> ${this._escape(facility.city)} ${this._escape(facility.state)} ${this._escape(facility.zip_code)}</div>
                        <div><strong>Phone:</strong> ${this._escape(facility.phone) || 'Not provided'}</div>
                        <div><strong>Permit Holder:</strong> ${this._escape(facility.permit_holder) || 'Not provided'}</div>
                    </div>
                </div>

                <div class="info-section" style="margin-bottom: 24px;">
                    <h3 style="margin: 0 0 12px 0; color: #1f2937; font-size: 16px; border-bottom: 2px solid #e5e7eb; padding-bottom: 4px;">Inspection Details</h3>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; font-size: 14px;">
                        <div><strong>Date:</strong> ${this._escape(data.inspection_date) || 'Not provided'}</div>
                        <div><strong>Type:</strong> ${this._escape(data.inspection_type) || 'Not provided'}</div>
                        <div><strong>Inspector:</strong> ${this._escape(data.inspector_name) || 'Not provided'}</div>
                        <div><strong>Inspector Phone:</strong> ${this._escape(data.inspector_phone) || 'Not provided'}</div>
                        <div><strong>Total Violations:</strong> ${violationCount}</div>
                        <div><strong>Inspection ID:</strong> ${this._escape(data.inspection_id) || 'Not provided'}</div>
                    </div>
                </div>

                ${data.report_notes ? `
                <div class="info-section" style="margin-bottom: 24px;">
                    <h3 style="margin: 0 0 12px 0; color: #1f2937; font-size: 16px; border-bottom: 2px solid #e5e7eb; padding-bottom: 4px;">Inspector Notes</h3>
                    <div style="background: #f9fafb; padding: 16px; border-radius: 8px; border-left: 4px solid #3b82f6; font-size: 14px; line-height: 1.5;">
                        ${this._escape(data.report_notes)}
                    </div>
                </div>
                ` : ''}

                ${violationCount > 0 ? `
                <div class="info-section">
                    <h3 style="margin: 0 0 12px 0; color: #1f2937; font-size: 16px; border-bottom: 2px solid #e5e7eb; padding-bottom: 4px;">Violations Summary</h3>
                    <div style="background: #fef3c7; padding: 16px; border-radius: 8px; border-left: 4px solid #f59e0b; font-size: 14px;">
                        <p style="margin: 0 0 8px 0;"><strong>${violationCount} violation${violationCount === 1 ? '' : 's'} found</strong></p>
                        <p style="margin: 0; color: #92400e;">
                            <span style="cursor: pointer; text-decoration: underline;" onclick="window.violationModal.show(${data.index || 0})">Click here to view detailed violations</span>
                        </p>
                    </div>
                </div>
                ` : `
                <div class="info-section">
                    <h3 style="margin: 0 0 12px 0; color: #1f2937; font-size: 16px; border-bottom: 2px solid #e5e7eb; padding-bottom: 4px;">Violations Summary</h3>
                    <div style="background: #d1fae5; padding: 16px; border-radius: 8px; border-left: 4px solid #10b981; font-size: 14px; color: #065f46;">
                        <strong>✓ No violations found - Facility passed inspection</strong>
                    </div>
                </div>
                `}
            </div>
        `;
    }

    _buildReadOnlySection(sapphireManaged, managementCompany) {
        return `
            <div class="info-section" style="margin-bottom: 24px;">
                <h3 style="margin: 0 0 12px 0; color: #1f2937; font-size: 16px; border-bottom: 2px solid #e5e7eb; padding-bottom: 4px;">Management Information</h3>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; font-size: 14px;">
                    <div><strong>Sapphire Managed:</strong> 
                        <span style="color: ${sapphireManaged ? '#10b981' : '#6b7280'};">
                            ${sapphireManaged ? '✓ Yes' : '✗ No'}
                        </span>
                    </div>
                    <div><strong>Management Company:</strong> ${this._escape(managementCompany) || 'Not specified'}</div>
                </div>
            </div>
        `;
    }

    _buildEditSection(sapphireManaged, managementCompany) {
        // FIXED: Handle empty companies array gracefully
        let companiesOptions = '';
        if (this.managementCompanies && this.managementCompanies.length > 0) {
            companiesOptions = this.managementCompanies.map(company => 
                `<option value="${this._escape(company)}" ${company === managementCompany ? 'selected' : ''}>${this._escape(company)}</option>`
            ).join('');
        }

        return `
            <div class="info-section" style="margin-bottom: 24px; background: #fef3c7; padding: 16px; border-radius: 8px; border-left: 4px solid #f59e0b;">
                <h3 style="margin: 0 0 16px 0; color: #1f2937; font-size: 16px;">Edit Management Information</h3>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; align-items: start;">
                    <div>
                        <label style="display: flex; align-items: center; gap: 8px; font-size: 14px; cursor: pointer;">
                            <input type="checkbox" id="sapphire-managed-checkbox" ${sapphireManaged ? 'checked' : ''} style="width: 16px; height: 16px;">
                            <strong>Managed by Sapphire Pool Service</strong>
                        </label>
                    </div>
                    <div>
                        <label style="display: block; font-size: 14px; font-weight: bold; margin-bottom: 4px;">Management Company:</label>
                        <input type="text" id="management-company-input" list="management-companies" value="${this._escape(managementCompany)}" 
                               placeholder="Enter company name..."
                               style="width: 100%; padding: 6px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 14px;">
                        <datalist id="management-companies">
                            ${companiesOptions}
                        </datalist>
                        ${this.managementCompanies.length === 0 ? 
                            '<div style="font-size: 12px; color: #6b7280; margin-top: 2px;">No existing companies - type to add new</div>' : 
                            '<div style="font-size: 12px; color: #6b7280; margin-top: 2px;">Select existing or type new company</div>'
                        }
                    </div>
                </div>
                <div style="margin-top: 16px; display: flex; gap: 8px;">
                    <button onclick="window.reportModal.saveManagement()" style="background: #10b981; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 14px;">
                        Save Changes
                    </button>
                    <button onclick="window.reportModal.toggleEditMode()" style="background: #6b7280; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 14px;">
                        Cancel
                    </button>
                </div>
            </div>
        `;
    }

    _escape(text = '') {
        if (text === null || text === undefined) return '';
        const map = {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'};
        return String(text).replace(/[&<>"']/g, m => map[m]);
    }
}

window.reportModal = new ReportModal();
