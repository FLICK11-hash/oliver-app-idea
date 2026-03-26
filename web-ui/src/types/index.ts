export type Gender = "Male" | "Female";

export type Role =
  | "KIDS_TEACHER"
  | "KIDS_ASSISTANT"
  | "SETUP"
  | "COFFEE";

export interface Volunteer {
  id: string;
  name: string;
  gender: Gender;
  active: boolean;
  archived: boolean;
  phone: string | null;
  email: string | null;
  canTeachKids: boolean;
  canAssistKids: boolean;
  canSetup: boolean;
  canCoffee: boolean;
  kidsCoupleGroup: string | null;
}

export interface ServeRecord {
  id: string;
  date: string;
  volunteerId: string;
  role: Role;
}

export interface Schedule {
  date: string;
  kidsTeacher: string | null;
  kidsAssistants: string[];
  setup: string[];
  coffee: string | null;
}

export interface ValidationResult {
  errors: string[];
  warnings: string[];
}

export interface Candidate {
  volunteer: Volunteer;
  role: Role;
  priority: number;
  rawScore: number;
  stats: {
    totalServes: number;
    servesThisMonth: number;
    lastServedDate: string | null;
    sundaysSinceLastServed: number | null;
    servedLastSunday: boolean;
    neverServed: boolean;
  };
}

export interface DashboardData {
  totalVolunteers: number;
  activeVolunteers: number;
  totalServeRecords: number;
  topCandidates: Record<Role, Candidate[]>;
}