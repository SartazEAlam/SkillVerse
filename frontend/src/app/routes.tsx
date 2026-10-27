import { createBrowserRouter } from 'react-router-dom'
import { Shell } from '../components/layout/Shell'
import { DashboardPage } from '../pages/DashboardPage'
import { ExplorePage } from '../pages/ExplorePage'
import { SkillsPage } from '../pages/SkillsPage'
import { CourseOverviewPage } from '../pages/CourseOverviewPage'
import { LoginPage } from '../pages/LoginPage'
import { RegisterPage } from '../pages/RegisterPage'
import { ProfilePage } from '../pages/ProfilePage'
import { NotFoundPage } from '../pages/NotFoundPage'
import { LessonWorkspacePage } from '../pages/LessonWorkspacePage'
import { CreatorStudioPage } from '../pages/CreatorStudioPage'
import { CourseEditorPage } from '../pages/CourseEditorPage'

export const router = createBrowserRouter([
  {
    path: '/creator/courses/:courseId/preview/:lessonSlug',
    element: <LessonWorkspacePage />,
  },
  {
    path: '/creator/courses/:courseId/preview',
    element: <LessonWorkspacePage />,
  },
  {
    path: '/creator/courses/:courseId',
    element: <CourseEditorPage />,
  },
  {
    path: '/learn/:courseSlug/:moduleSlug/:lessonSlug',
    element: <LessonWorkspacePage />,
  },
  {
    path: '/learn/:courseSlug/:lessonSlug',
    element: <LessonWorkspacePage />,
  },
  {
    path: '/learn/:courseSlug',
    element: <LessonWorkspacePage />,
  },
  {
    path: '/courses/:courseSlug/learn/:lessonSlug',
    element: <LessonWorkspacePage />,
  },
  {
    path: '/',
    element: <Shell />,
    children: [
      {
        index: true,
        element: <DashboardPage />,
      },
      {
        path: 'explore',
        element: <ExplorePage />,
      },
      {
        path: 'skills',
        element: <SkillsPage />,
      },
      {
        path: 'creator',
        element: <CreatorStudioPage />,
      },
      {
        path: 'courses/:slug',
        element: <CourseOverviewPage />,
      },
      {
        path: 'login',
        element: <LoginPage />,
      },
      {
        path: 'register',
        element: <RegisterPage />,
      },
      {
        path: 'profile',
        element: <ProfilePage />,
      },
      {
        path: '*',
        element: <NotFoundPage />,
      },
    ],
  },
])
