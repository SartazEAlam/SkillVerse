import { createBrowserRouter } from 'react-router-dom'
import { Shell } from '../components/layout/Shell'
import { DashboardPage } from '../pages/DashboardPage'
import { ExplorePage } from '../pages/ExplorePage'
import { SkillsPage } from '../pages/SkillsPage'
import { CourseOverviewPage } from '../pages/CourseOverviewPage'
import { NotFoundPage } from '../pages/NotFoundPage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Shell />,
    children: [
      {
        index: true,
        element: <DashboardPage />
      },
      {
        path: 'explore',
        element: <ExplorePage />
      },
      {
        path: 'skills',
        element: <SkillsPage />
      },
      {
        path: 'courses/:slug',
        element: <CourseOverviewPage />
      },
      {
        path: '*',
        element: <NotFoundPage />
      }
    ]
  }
])
