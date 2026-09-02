export enum UserRole {
  ADMIN = 'ADMIN',
  CASHIER = 'CASHIER'
}

export type CurrencyCode = 'SYP' | 'USD' | 'EUR';

export interface User {
  id: number;
  name: string;
  role: string;
  email: string;
  status: string;
}

export interface Branch {
  id: number;
  name: string;
  location: string;
  isOffline?: boolean;
}

export interface ShiftFuelDetail {
  fuelType: string;
  expectedSales: number;
  actualSales: number;
  litersSold: number;
  remainingLiters: number;
}

export interface InventoryItem {
  id: number;
  fuelType: string;
  currentCapacity: number;
  maxCapacity: number;
  lastRefill: string;
  predictedEmptyDate: string;
  recommendationAction?: string;
  recommendationReason?: string;
  recommendationConfidence?: number;
}

export interface ShiftReport {
  id: number;
  userId?: number;
  userName?: string;
  cashierId?: number;
  cashierName?: string;
  branchId?: number;
  startTime: string;
  endTime?: string;
  status: 'OPEN' | 'PENDING_REVIEW' | 'CLOSED';
  openingCash: number;
  totalExpectedCash?: number;
  totalActualCash?: number;
  discrepancy?: number;
  openingFuelLevels?: {
    fuelType: string;
    amount: number;
    price: number;
  }[];
  fuelDetails?: ShiftFuelDetail[];
  /** التاريخ الفعلي لبداية الوردية (ISO) لعرضه في السجلات */
  startDateTime?: string;
}

export interface FuelType {
  id: number;
  name: string;
  pricePerLiter: number;
  color: string;
}

export interface Alert {
  id: number;
  type: string;
  message: string;
  severity: string;
  timestamp: string;
  isRead: boolean;
}

export interface Transaction {
  id: number;
  shiftId: number;
  userId: number;
  pumpId: number;
  fuelType: string;
  liters: number;
  amount: number;
  paymentMethod: string;
  timestamp: string;
}

export interface SaleRecord {
  id: number;
  pumpId: number;
  fuelType: string;
  amount: number;
  liters: number;
  timestamp: string;
}

export interface CashierPerformance {
  userId: number;
  totalSales: number;
  shiftsCount: number;
  averageEfficiency: number;
  cashDiscrepancyRate: number;
  customerRating: number;
  aiSummary: string;
  badges: string[];
  recommendation: 'PROMOTE' | 'TRAIN' | 'MONITOR' | 'BONUS';
  fuelSales?: {
    [fuelType: string]: {
      liters: number;
      amount: number;
    };
  };
}

// شركة مورد: الأنواع التي تتعامل معها + الأسعار المتفق عليها + تفاصيل التواصل
export interface SupplierCompany {
  name: string;
  fuels: string[];
  agreedPrices: { [fuelType: string]: number };
  email?: string;
  phone?: string;
}