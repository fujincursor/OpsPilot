import { Navigate, Outlet } from 'react-router-dom'
import { authService } from '../../services/authService'

export default function RequireAuth() {
  if (!authService.getToken()) {
    return <Navigate to="/login" replace />
  }
  return <Outlet />
}
