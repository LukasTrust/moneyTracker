import React, { useState } from 'react';
import Modal from '../common/Modal';
import Input from '../common/Input';
import Button from '../common/Button';

/**
 * Modal zum Erstellen eines neuen Kontos
 */
export default function CreateAccountModal({ isOpen, onClose, onCreate }) {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    currency: 'EUR',
    initial_balance: '0.00',
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    // Clear error when user types
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: '' }));
    }
  };

  const validate = () => {
    const newErrors = {};
    if (!formData.name.trim()) {
      newErrors.name = 'Kontoname ist erforderlich';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    try {
      // Convert initial_balance to number before sending
      const dataToSend = {
        ...formData,
        initial_balance: parseFloat(formData.initial_balance) || 0.0,
      };
      await onCreate(dataToSend);
      // Reset form
      setFormData({ name: '', description: '', currency: 'EUR', initial_balance: '0.00' });
      setErrors({});
      onClose();
    } catch (error) {
      setErrors({ submit: error.response?.data?.message || 'Fehler beim Erstellen' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Neues Konto erstellen"
      footer={
        <div className="flex gap-3 justify-end">
          <Button variant="secondary" onClick={onClose} disabled={loading} title="Abbrechen" aria-label="Abbrechen">
            Abbrechen
          </Button>
          <Button onClick={handleSubmit} loading={loading} title="Konto erstellen" aria-label="Konto erstellen">
            Konto erstellen
          </Button>
        </div>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Kontoname"
          name="name"
          value={formData.name}
          onChange={handleChange}
          error={errors.name}
          required
          placeholder="z.B. Girokonto"
        />

        <div>
          <label className="label">Beschreibung</label>
          <textarea
            name="description"
            value={formData.description}
            onChange={handleChange}
            className="input"
            rows="3"
            placeholder="Optional: Zusätzliche Informationen"
            aria-label="Beschreibung"
          />
        </div>

        <div>
          <label className="label">Währung</label>
          <select
            name="currency"
            value={formData.currency}
            onChange={handleChange}
            className="input"
          >
            <option value="EUR">EUR (€)</option>
            <option value="USD">USD ($)</option>
            <option value="GBP">GBP (£)</option>
            <option value="CHF">CHF (Fr)</option>
          </select>
        </div>

        <Input
          label="Startguthaben"
          name="initial_balance"
          type="number"
          step="0.01"
          value={formData.initial_balance}
          onChange={handleChange}
          placeholder="0.00"
          helperText="Geben Sie den aktuellen Kontostand ein, falls bereits Geld vorhanden ist"
        />

        {errors.submit && (
          <p className="text-sm text-red-600">{errors.submit}</p>
        )}
      </form>
    </Modal>
  );
}
