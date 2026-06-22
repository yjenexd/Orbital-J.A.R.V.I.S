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
    user_id: string;
}

export type UserSchedule = CalendarEvent[];

export interface Task {
    task_id: number;
    title: string;
    source: string;
    deadline: string;
    completed:boolean;
    user_id: string;
    priority: string;
    email_id?: number | null;
    triage_rationale?: string | null;
    priority_score: number;
}

export interface Email {
    email_id: number; // int8
    date: string;     // timestamp
    sender: string;
    summary: string;
    user_id: string;  // int8 (Foreign Key)
    subject: string;
    urgency: 'low' | 'medium' | 'high'; // Custom email_urgency type
}

/**
 * Represents a single message bubble in the chat interface.
 */
export interface ChatMessage {
  /** Unique identifier for the message */  
  message_id: number;

  user_id: string;
  /** The text content of the message */
  content: string;
  /** Identifies whether the message is from the human or the AI */
  role: 'user' | 'system' | 'system';
  /** Unix timestamp of when the message was created */
  created_at: string;
}

