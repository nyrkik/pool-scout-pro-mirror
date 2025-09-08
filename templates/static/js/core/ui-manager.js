/**
* UI Manager - Pool Scout Pro
* Centralized UI state management and DOM manipulation.
*/

class UIManager {
  constructor() {
      this.elements = {
          searchButton: document.getElementById('searchButton'),
          dateInput: document.getElementById('searchDate'),
          resultsBody: document.getElementById('reports-table-body'),
          resultsCount: document.getElementById('results-count'),
          onFileCount: document.getElementById('on-file-count'),
          currentSearchDate: document.getElementById('current-search-date')
      };
  }

  showProgress(message, options = {}) {
      const progressEl = document.getElementById("header-progress");
      const messageEl = document.getElementById("header-message");
      const activityEl = document.getElementById("header-activity");

      if (!progressEl || !messageEl) return;

      messageEl.textContent = message;
      progressEl.style.display = "block";

      if (options.showActivity && activityEl) {
          const percentEl = activityEl.querySelector(".activity-percent");
          if (options.percentage !== undefined && percentEl) {
              percentEl.textContent = options.percentage + "%";
          }
          activityEl.style.display = "flex";
      } else if (activityEl) {
          activityEl.style.display = "none";
      }
  }

  hideProgress() {
      const progressEl = document.getElementById("header-progress");
      if (progressEl) progressEl.style.display = "none";
  }

  renderSearchResults(facilities) {
      // FIXED: Use search results directly without faulty merging
      // The search API already returns facilities with correct saved status
      this._renderTable(facilities, false);
  }

  renderSavedReports(reports) {
      const facilities = reports.map(r => ({...r.facility, saved: true, violations: r.violations}));
      this._renderTable(facilities, true);
  }

  _renderTable(facilities, isSavedReport) {
      if (!this.elements.resultsBody) return;

      if (!facilities || facilities.length === 0) {
          this.elements.resultsBody.innerHTML = `<tr><td colspan="4" class="text-center text-muted">No reports found.</td></tr>`;
          return;
      }

      let html = '';
      facilities.forEach((facility, index) => {
          html += this._renderFacilityRow(facility, index, isSavedReport);
      });

      this.elements.resultsBody.innerHTML = html;
      this.refreshIcons();
  }

  _renderFacilityRow(facility, index, isSavedReport) {
      const address = this._getCleanAddress(facility, isSavedReport);
      const name = this.escapeHtml(facility.name || '');
      const facilityTypeIcon = this.getFacilityTypeIcon(facility.program_identifier);
      const rowClass = facility.saved ? 'facility-row-saved' : 'facility-row-unsaved';

      return `
          <tr data-facility-index="${index}" data-inspection-id="${facility.inspection_id || ''}" class="${rowClass}">
              <td class="text-center">${index + 1}</td>
              <td class="text-center">${facilityTypeIcon}</td>
              <td>
                  <div>
                      <div style="font-weight: 500; cursor: pointer;" onclick="showFullReport(${index}, ${isSavedReport})">${name}</div>
                      <div style="font-size: 13px; color: #6b7280;">${address}</div>
                  </div>
              </td>
              <td>${this.renderTopFindings(facility, index)}</td>
          </tr>
      `;
  }

  _getCleanAddress(facility, isSavedReport) {
      if (isSavedReport) {
          const street = facility.street_address || '';
          const city = facility.city || '';
          return city ? `${street}, ${city}` : street;
      } else {
          let address = facility.display_address || '';
          if (!address) return 'Address not available';
          return address.replace(/,?\s*CA\s+\d{5}(-\d{4})?.*$/, '').trim();
      }
  }

  updateResultsCounts(total = 0, onFile = 0) {
      if (this.elements.resultsCount) {
          this.elements.resultsCount.textContent = total;
      }
      if (this.elements.onFileCount) {
          this.elements.onFileCount.textContent = onFile;
      }
  }

  updateUnsavedCount(unsavedCount) {
      if (this.elements.resultsCount) {
          this.elements.resultsCount.textContent = unsavedCount;
      }
  }

  setCurrentSearchDate(date) {
      if (this.elements.currentSearchDate) {
          this.elements.currentSearchDate.textContent = date || '-';
      }
  }

  clearResults() {
      if (this.elements.resultsBody) {
          this.elements.resultsBody.innerHTML = `<tr><td colspan="4" class="text-center text-muted">No search performed yet</td></tr>`;
      }
      this.updateResultsCounts(0, 0);
  }

  renderTopFindings(facility, index) {
      return facility.saved ? 'Click to view details' : 'Not saved yet';
  }

  getFacilityTypeIcon(pid) {
      return pid && pid.toUpperCase().includes('SPA') ?
          '<i data-lucide="waves" title="Spa"></i>' :
          '<i data-lucide="droplets" title="Pool"></i>';
  }

  refreshIcons() {
      if (window.lucide) {
          window.lucide.createIcons();
      }
  }

  escapeHtml(text = '') {
      const map = {
          '&': '&amp;',
          '<': '&lt;',
          '>': '&gt;',
          '"': '&quot;',
          "'": '&#039;'
      };
      return text.replace(/[&<>"']/g, m => map[m]);
  }

  setSaveButtonProcessing(isProcessing) {
      console.log(`setSaveButtonProcessing called: ${isProcessing}`);
  }
}

window.uiManager = new UIManager();
