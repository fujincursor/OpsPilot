import api from './api'
import { authService } from './authService'
import type { ReviewItem, ReviewComment, ReviewDecision, Notification } from '../types'

interface ReviewListResponse {
  items: ReviewItem[]
  total: number
}

interface CommentListResponse {
  items: ReviewComment[]
}

interface ApiNotification {
  id: string
  type: string
  title: string
  content: string
  review_item_id?: string
  is_read: boolean
  created_at: string
}

interface NotificationListResponse {
  items: ApiNotification[]
  unread_count: number
}

function reviewerName(): string {
  return authService.getUser()?.username || 'unknown'
}

function mapReview(item: ReviewItem & { comments?: unknown[] }): ReviewItem {
  return {
    ...item,
    comments_count: item.comments_count ?? item.comments?.length ?? 0,
  }
}

function mapDecision(item: ReviewDecision): ReviewDecision {
  const aliases: Record<string, ReviewDecision['decision']> = {
    approve: 'approved',
    reject: 'rejected',
    request_revision: 'revision_requested',
  }
  return {
    ...item,
    decision: aliases[item.decision] || item.decision,
  }
}

export const reviewService = {
  async getPendingReviews(): Promise<ReviewItem[]> {
    const response = await api.get<ReviewListResponse>('/reviews/pending')
    return response.data.items.map((item) => mapReview(item))
  },

  async getReviewDetail(reviewId: string): Promise<ReviewItem> {
    const response = await api.get<ReviewItem & { comments?: unknown[] }>(`/reviews/${reviewId}`)
    return mapReview(response.data)
  },

  async approve(reviewId: string, reason: string): Promise<ReviewDecision> {
    const response = await api.post<{ decisions?: ReviewDecision[] }>(`/reviews/${reviewId}/approve`, { reason }, {
      params: { reviewer: reviewerName() },
      timeout: 120000,
    })
    const latest = response.data.decisions?.[response.data.decisions.length - 1]
    if (!latest) throw new Error('审核结果未返回')
    return mapDecision(latest)
  },

  async reject(reviewId: string, reason: string): Promise<ReviewDecision> {
    const response = await api.post<{ decisions?: ReviewDecision[] }>(`/reviews/${reviewId}/reject`, { reason }, {
      params: { reviewer: reviewerName() },
      timeout: 120000,
    })
    const latest = response.data.decisions?.[response.data.decisions.length - 1]
    if (!latest) throw new Error('审核结果未返回')
    return mapDecision(latest)
  },

  async requestRevision(reviewId: string, comments: string): Promise<ReviewDecision> {
    const response = await api.post<{ decisions?: ReviewDecision[] }>(
      `/reviews/${reviewId}/request-revision`,
      { comments },
      { params: { reviewer: reviewerName() }, timeout: 120000 }
    )
    const latest = response.data.decisions?.[response.data.decisions.length - 1]
    if (!latest) throw new Error('审核结果未返回')
    return mapDecision(latest)
  },

  async addComment(reviewId: string, content: string): Promise<ReviewComment> {
    const response = await api.post<ReviewComment>(
      `/reviews/${reviewId}/comments`,
      { content },
      { params: { author: reviewerName() } }
    )
    return response.data
  },

  async getComments(reviewId: string): Promise<ReviewComment[]> {
    const response = await api.get<CommentListResponse>(`/reviews/${reviewId}/comments`)
    return response.data.items
  },

  async getDecisions(reviewId: string): Promise<ReviewDecision[]> {
    const response = await api.get<{ decisions?: ReviewDecision[] }>(`/reviews/${reviewId}`)
    return (response.data.decisions || []).map(mapDecision)
  },

  async getNotifications(): Promise<Notification[]> {
    const user = authService.getUser()
    if (!user) return []
    const response = await api.get<NotificationListResponse>('/notifications', {
      params: { user_id: user.id },
    })
    return response.data.items.map((item) => ({
      id: item.id,
      type: item.type as Notification['type'],
      title: item.title,
      message: item.content,
      read: item.is_read,
      created_at: item.created_at,
      link: item.review_item_id ? `/reviews/${item.review_item_id}` : undefined,
    }))
  },

  async markNotificationRead(notificationId: string): Promise<void> {
    await api.post(`/notifications/${notificationId}/read`)
  },

  async markAllNotificationsRead(): Promise<void> {
    const user = authService.getUser()
    if (!user) return
    await api.post('/notifications/read-all', null, { params: { user_id: user.id } })
  },

  async getUnreadCount(): Promise<number> {
    const user = authService.getUser()
    if (!user) return 0
    const response = await api.get<NotificationListResponse>('/notifications', {
      params: { user_id: user.id, page_size: 1 },
    })
    return response.data.unread_count
  },
}
