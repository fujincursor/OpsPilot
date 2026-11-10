import api from './api'
import type { ReviewItem, ReviewComment, ReviewDecision, Notification } from '../types'

export const reviewService = {
  async getPendingReviews(projectId?: string): Promise<ReviewItem[]> {
    const params = projectId ? { project_id: projectId } : {}
    const response = await api.get('/reviews', { params })
    return response.data.data
  },

  async getReviewDetail(reviewId: string): Promise<ReviewItem> {
    const response = await api.get(`/reviews/${reviewId}`)
    return response.data.data
  },

  async approve(reviewId: string, reason: string): Promise<ReviewDecision> {
    const response = await api.post(`/reviews/${reviewId}/approve`, { reason })
    return response.data.data
  },

  async reject(reviewId: string, reason: string): Promise<ReviewDecision> {
    const response = await api.post(`/reviews/${reviewId}/reject`, { reason })
    return response.data.data
  },

  async requestRevision(reviewId: string, comments: string): Promise<ReviewDecision> {
    const response = await api.post(`/reviews/${reviewId}/request-revision`, { comments })
    return response.data.data
  },

  async addComment(reviewId: string, content: string): Promise<ReviewComment> {
    const response = await api.post(`/reviews/${reviewId}/comments`, { content })
    return response.data.data
  },

  async getComments(reviewId: string): Promise<ReviewComment[]> {
    const response = await api.get(`/reviews/${reviewId}/comments`)
    return response.data.data
  },

  async getDecisions(reviewId: string): Promise<ReviewDecision[]> {
    const response = await api.get(`/reviews/${reviewId}/decisions`)
    return response.data.data
  },

  async getNotifications(): Promise<Notification[]> {
    const response = await api.get('/notifications')
    return response.data.data
  },

  async markNotificationRead(notificationId: string): Promise<void> {
    await api.patch(`/notifications/${notificationId}/read`)
  },

  async markAllNotificationsRead(): Promise<void> {
    await api.patch('/notifications/read-all')
  },

  async getUnreadCount(): Promise<number> {
    const response = await api.get('/notifications/unread-count')
    return response.data.data.count
  },
}
