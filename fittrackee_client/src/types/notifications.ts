import type { IReportForModerator } from '@/types/reports'
import type { IUserReportAction, IUserProfile } from '@/types/user'
import type { IComment, IWorkout } from '@/types/workouts'

export type TNotificationType =
  | 'account_creation'
  | 'comment_like'
  | 'comment_reply'
  | 'comment_suspension'
  | 'comment_unsuspension'
  | 'follow'
  | 'follow_request'
  | 'mention'
  | 'report'
  | 'suspension_appeal'
  | 'user_warning'
  | 'user_warning_appeal'
  | 'user_warning_lifting'
  | 'workout_comment'
  | 'workout_like'
  | 'workout_suspension'
  | 'workout_unsuspension'

export interface INotification {
  report_action?: IUserReportAction
  comment?: IComment
  created_at: string
  id: number
  from?: IUserProfile
  marked_as_read: boolean
  report?: IReportForModerator
  type: TNotificationType
  workout?: IWorkout
}

export interface INotificationsPayload {
  page?: number
  order?: string
  read_status?: boolean
  type?: TNotificationType
}

export interface INotificationPayload {
  notificationId: number
  markedAsRead: boolean
  currentQuery: INotificationsPayload
}
