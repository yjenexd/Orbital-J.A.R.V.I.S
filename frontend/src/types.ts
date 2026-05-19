export interface User {
    id: string;
    name: string;
}

export interface CalendarEvent {
    event_id: string;
    date: string;
    time: string;
    event: string;
    protected: boolean;
    user_id: number;
}

export type UserSchedule = CalendarEvent[];

export interface Task {
    task_id: string;
    task: string;
    origin: string;
    deadline: string;
    status:boolean;
    user_id: number;
}

export interface Email {
    email_id: string; // int8
    date: string;     // timestamp
    sender: string;
    summary: string;
    user_id: number;  // int8 (Foreign Key)
    subject: string;
    urgency: 'low' | 'medium' | 'high'; // Custom email_urgency type
}


//tasks needs a priority field
//need to add an email_id field to task to link tasks to emails (for email follow-up tasks)