import { Alert, InventoryItem, SaleRecord } from './types';

export const MOCK_INVENTORY: InventoryItem[] = [
  {
    id: 1,
    fuelType: 'بنزين 91',
    currentCapacity: 12500,
    maxCapacity: 50000,
    lastRefill: '2023-10-25',
    predictedEmptyDate: '2 أيام'
  },
  {
    id: 2,
    fuelType: 'بنزين 95',
    currentCapacity: 34000,
    maxCapacity: 45000,
    lastRefill: '2023-10-26',
    predictedEmptyDate: '10 أيام'
  },
  {
    id: 3,
    fuelType: 'ديزل',
    currentCapacity: 8000,
    maxCapacity: 60000,
    lastRefill: '2023-10-20',
    predictedEmptyDate: '24 ساعة'
  }
];

export const MOCK_ALERTS: Alert[] = [
  {
    id: 1,
    type: 'THEFT',
    message: 'اكتشاف شذوذ في المضخة رقم 4: تدفق وقود بدون تفويض.',
    severity: 'high',
    timestamp: 'منذ 10 دقائق',
    isRead: false
  },
  {
    id: 2,
    type: 'INVENTORY',
    message: 'مستوى الديزل منخفض جداً. يرجى طلب شحنة جديدة.',
    severity: 'medium',
    timestamp: 'منذ ساعة',
    isRead: false
  }
];

export const SALES_DATA = [
  { name: 'السبت', value: 4000 },
  { name: 'الأحد', value: 3000 },
  { name: 'الاثنين', value: 2000 },
  { name: 'الثلاثاء', value: 2780 },
  { name: 'الأربعاء', value: 1890 },
  { name: 'الخميس', value: 2390 },
  { name: 'الجمعة', value: 3490 },
];

export const RECENT_SALES: SaleRecord[] = [
  { id: 101, pumpId: 2, fuelType: 'بنزين 91', amount: 45, liters: 20, timestamp: '10:30 AM' },
  { id: 102, pumpId: 5, fuelType: 'بنزين 95', amount: 120, liters: 51, timestamp: '10:35 AM' },
  { id: 103, pumpId: 1, fuelType: 'ديزل', amount: 200, liters: 180, timestamp: '10:42 AM' },
];