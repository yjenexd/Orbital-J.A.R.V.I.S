export interface User {
    id: number;
    name: string;
}

export interface CalendarEvent {
    event_id: number;
    date: string;
    time: string;
    event: string;
    protected: boolean;
    user_id: number;
}

export type UserSchedule = CalendarEvent[];

export interface Task {
    task_id: number;
    task: string;
    origin: string;
    deadline: string;
    status:boolean;
    user_id: number;
    priority: number;
    email_id?: number | null;
}

export interface Email {
    email_id: number; // int8
    date: string;     // timestamp
    sender: string;
    summary: string;
    user_id: number;  // int8 (Foreign Key)
    subject: string;
    urgency: 'low' | 'medium' | 'high'; // Custom email_urgency type
}

